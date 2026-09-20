#!/usr/bin/env node
/**
 * Emit the TypeScript SDK's public surface as JSON, for the cross-SDK parity gate.
 *
 * Uses the TypeScript compiler's own parser rather than matching on text, so a
 * reformat, a comment or a multi-line signature cannot change the answer. Lives
 * inside sdk/typescript so `typescript` resolves from this package's own
 * node_modules after `npm ci`.
 *
 * Usage:  node scripts/extract-surface.mjs > surface.typescript.json
 */

import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const SRC = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'src')

// Mirrored from the server, and compared by value in the parity check: a new
// insight kind reaching one client and not the other is the drift this catches.
const TRACKED_CONSTANTS = [
  'INSIGHT_KINDS',
  'INSIGHT_TIERS',
  'INSIGHT_UNAVAILABLE_REASONS',
  'CONSTITUTIONAL_CODES',
]

function parse(name) {
  const path = resolve(SRC, name)
  return ts.createSourceFile(path, readFileSync(path, 'utf8'), ts.ScriptTarget.Latest, true)
}

function isExported(node) {
  return (ts.getCombinedModifierFlags(node) & ts.ModifierFlags.Export) !== 0
}

function isPrivate(node) {
  return (ts.getCombinedModifierFlags(node) & ts.ModifierFlags.Private) !== 0
}

/** Public method names on a class, excluding the constructor and private members. */
function publicMethods(source, className) {
  let methods = null
  source.forEachChild((node) => {
    if (ts.isClassDeclaration(node) && node.name?.text === className) {
      methods = node.members
        .filter((m) => ts.isMethodDeclaration(m) && !isPrivate(m) && m.name)
        .map((m) => m.name.getText(source))
        .sort()
    }
  })
  if (methods === null) {
    console.error(`parity: class ${className} not found in the TypeScript client`)
    process.exit(1)
  }
  return methods
}

/** Exported class names, which is how the error hierarchy is declared. */
function exportedClasses(source) {
  const names = []
  source.forEachChild((node) => {
    if (ts.isClassDeclaration(node) && node.name && isExported(node)) names.push(node.name.text)
  })
  return names.sort()
}

/** Exported `const NAME = [...] as const` string arrays, read as real values. */
function constants(...sources) {
  const found = {}
  for (const source of sources) {
    source.forEachChild((node) => {
      if (!ts.isVariableStatement(node) || !isExported(node)) return
      for (const decl of node.declarationList.declarations) {
        const name = decl.name.getText(source)
        if (!TRACKED_CONSTANTS.includes(name) || !decl.initializer) continue
        // `[...] as const` wraps the array in an assertion expression.
        const init = ts.isAsExpression(decl.initializer)
          ? decl.initializer.expression
          : decl.initializer
        if (!ts.isArrayLiteralExpression(init)) {
          console.error(`parity: ${name} is not an array literal in the TypeScript client`)
          process.exit(1)
        }
        found[name] = init.elements.map((el) => {
          if (!ts.isStringLiteral(el)) {
            console.error(`parity: ${name} holds a non-string entry in the TypeScript client`)
            process.exit(1)
          }
          return el.text
        })
      }
    })
  }
  return found
}

const client = parse('client.ts')
const errors = parse('errors.ts')
const found = constants(client, errors)

const surface = {
  language: 'typescript',
  methods: publicMethods(client, 'AIOpsClient'),
  errors: exportedClasses(errors),
  constants: Object.fromEntries(TRACKED_CONSTANTS.map((key) => [key, found[key] ?? null])),
}

process.stdout.write(`${JSON.stringify(surface, null, 2)}\n`)
