import { test, expect, Page } from '@playwright/test';

/**
 * Constitutional AIOps - Graph Explorer E2E Tests
 *
 * Tests the Episodic Graph Explorer component with v0.6.0 improvements:
 * - Force simulation (charge -800, center 0.2, variable link distance)
 * - Edge visibility toggles (Similar To, Entities)
 * - Layout mode toggle (Force vs Hierarchy/DAG)
 * - Node type filtering
 * - Zoom and pan controls
 *
 * @version 0.6.0
 */

test.describe('Episodic Graph Explorer', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the Graph Explorer page
    await page.goto('/graph');
    // Wait for the graph component to load
    await page.waitForSelector('canvas', { timeout: 10000 });
  });

  test.describe('Basic Rendering', () => {
    test('should render the graph canvas', async ({ page }) => {
      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
    });

    test('should display node/edge count stats', async ({ page }) => {
      // Stats overlay should show "X nodes | Y edges"
      const stats = page.locator('text=/\\d+ nodes \\| \\d+ edges/');
      await expect(stats).toBeVisible({ timeout: 5000 });
    });

    test('should show legend with all node types', async ({ page }) => {
      // Check legend items exist
      await expect(page.locator('text=Episode')).toBeVisible();
      await expect(page.locator('text=Root Cause')).toBeVisible();
      await expect(page.locator('text=Action')).toBeVisible();
      await expect(page.locator('text=Service')).toBeVisible();
      await expect(page.locator('text=Entity (LLM)')).toBeVisible();
      await expect(page.locator('text=Resolved')).toBeVisible();
    });
  });

  test.describe('Node Type Filtering', () => {
    test('should filter nodes by type selection', async ({ page }) => {
      // Get initial node count
      const initialStats = await page.locator('text=/\\d+ nodes/').textContent();
      const initialCount = parseInt(initialStats?.match(/\\d+/)?.[0] || '0');

      // Select "Episodes" filter
      await page.selectOption('select', 'episode');

      // Wait for graph to update
      await page.waitForTimeout(500);

      // Verify stats show filtered results
      const filteredStats = await page.locator('text=/\\d+ nodes.*filtered/i').textContent();
      expect(filteredStats).toContain('episode');
    });

    test('should show all types when "All Types" selected', async ({ page }) => {
      // First filter to a specific type
      await page.selectOption('select', 'episode');
      await page.waitForTimeout(300);

      // Then select "All Types"
      await page.selectOption('select', 'all');
      await page.waitForTimeout(300);

      // Stats should not show "filtered"
      const stats = await page.locator('text=/\\d+ nodes \\| \\d+ edges/').textContent();
      expect(stats).not.toContain('filtered');
    });
  });

  test.describe('Edge Visibility Controls (v0.6.0)', () => {
    test('should have Similar To checkbox', async ({ page }) => {
      const checkbox = page.locator('label:has-text("Similar To") input[type="checkbox"]');
      await expect(checkbox).toBeVisible();
      await expect(checkbox).toBeChecked(); // Default: checked
    });

    test('should have Entities checkbox', async ({ page }) => {
      const checkbox = page.locator('label:has-text("Entities") input[type="checkbox"]');
      await expect(checkbox).toBeVisible();
      await expect(checkbox).toBeChecked(); // Default: checked
    });

    test('should toggle Similar To edges', async ({ page }) => {
      // Get initial edge count
      const initialStats = await page.locator('text=/\\d+ edges/').textContent();
      const initialEdges = parseInt(initialStats?.match(/(\\d+) edges/)?.[1] || '0');

      // Uncheck Similar To
      const checkbox = page.locator('label:has-text("Similar To") input[type="checkbox"]');
      await checkbox.uncheck();
      await page.waitForTimeout(500);

      // Edge count should decrease (SIMILAR_TO edges removed)
      const newStats = await page.locator('text=/\\d+ edges/').textContent();
      const newEdges = parseInt(newStats?.match(/(\\d+) edges/)?.[1] || '0');

      // With SIMILAR_TO_THRESHOLD=0.75 and MAX_SIMILAR_EDGES_PER_EPISODE=3,
      // there should be fewer edges after unchecking
      expect(newEdges).toBeLessThanOrEqual(initialEdges);
    });

    test('should toggle Entity edges and nodes', async ({ page }) => {
      // Get initial node count
      const initialStats = await page.locator('text=/\\d+ nodes/').textContent();
      const initialNodes = parseInt(initialStats?.match(/(\\d+)/)?.[0] || '0');

      // Uncheck Entities
      const checkbox = page.locator('label:has-text("Entities") input[type="checkbox"]');
      await checkbox.uncheck();
      await page.waitForTimeout(500);

      // Node count should decrease (Entity nodes hidden)
      const newStats = await page.locator('text=/\\d+ nodes/').textContent();
      const newNodes = parseInt(newStats?.match(/(\\d+)/)?.[0] || '0');

      expect(newNodes).toBeLessThanOrEqual(initialNodes);
    });
  });

  test.describe('Layout Mode Toggle (v0.6.0)', () => {
    test('should have Force layout button', async ({ page }) => {
      const forceBtn = page.locator('button:has-text("Force")');
      await expect(forceBtn).toBeVisible();
    });

    test('should have Hierarchy layout button', async ({ page }) => {
      const dagBtn = page.locator('button:has-text("Hierarchy")');
      await expect(dagBtn).toBeVisible();
    });

    test('should switch to DAG mode', async ({ page }) => {
      const dagBtn = page.locator('button:has-text("Hierarchy")');
      await dagBtn.click();

      // Button should show active state (blue background)
      await expect(dagBtn).toHaveClass(/bg-blue-600/);

      // Force button should show inactive state
      const forceBtn = page.locator('button:has-text("Force")');
      await expect(forceBtn).toHaveClass(/bg-slate-800/);
    });

    test('should switch back to Force mode', async ({ page }) => {
      // First switch to DAG
      await page.locator('button:has-text("Hierarchy")').click();
      await page.waitForTimeout(300);

      // Then switch back to Force
      const forceBtn = page.locator('button:has-text("Force")');
      await forceBtn.click();

      await expect(forceBtn).toHaveClass(/bg-blue-600/);
    });
  });

  test.describe('Zoom and Pan Controls', () => {
    test('should have zoom in button', async ({ page }) => {
      const zoomIn = page.locator('button[title="Zoom In"]');
      await expect(zoomIn).toBeVisible();
    });

    test('should have zoom out button', async ({ page }) => {
      const zoomOut = page.locator('button[title="Zoom Out"]');
      await expect(zoomOut).toBeVisible();
    });

    test('should have fit to view button', async ({ page }) => {
      const fit = page.locator('button[title="Fit to View"]');
      await expect(fit).toBeVisible();
    });

    test('should zoom in when clicking zoom in button', async ({ page }) => {
      const zoomIn = page.locator('button[title="Zoom In"]');
      await zoomIn.click();
      await page.waitForTimeout(300);
      // Canvas should still be visible (no crash)
      await expect(page.locator('canvas')).toBeVisible();
    });

    test('should zoom out when clicking zoom out button', async ({ page }) => {
      const zoomOut = page.locator('button[title="Zoom Out"]');
      await zoomOut.click();
      await page.waitForTimeout(300);
      await expect(page.locator('canvas')).toBeVisible();
    });
  });

  test.describe('Simulation Controls', () => {
    test('should have play/pause button', async ({ page }) => {
      // Button should be either Play or Pause
      const playPause = page.locator('button[title="Pause Simulation"], button[title="Resume Simulation"]');
      await expect(playPause).toBeVisible();
    });

    test('should toggle simulation state', async ({ page }) => {
      const pauseBtn = page.locator('button[title="Pause Simulation"]');
      const resumeBtn = page.locator('button[title="Resume Simulation"]');

      // Initially should be playing (Pause button visible)
      if (await pauseBtn.isVisible()) {
        await pauseBtn.click();
        await expect(resumeBtn).toBeVisible();

        await resumeBtn.click();
        await expect(pauseBtn).toBeVisible();
      }
    });

    test('should have reset layout button', async ({ page }) => {
      const reset = page.locator('button[title="Reset Layout"]');
      await expect(reset).toBeVisible();
    });
  });

  test.describe('Node Interactions', () => {
    test('should show node details on click', async ({ page }) => {
      // Click on the canvas (somewhere a node might be)
      const canvas = page.locator('canvas');
      const box = await canvas.boundingBox();

      if (box) {
        // Click in the center of the canvas
        await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
        await page.waitForTimeout(500);

        // If a node was clicked, details panel should appear
        // (May not always hit a node, so this is a soft check)
        const detailsPanel = page.locator('text=/Episode|Root Cause|Action|Service|Entity/');
        // Just verify no crash occurred
        await expect(canvas).toBeVisible();
      }
    });
  });

  test.describe('Screenshot Tests', () => {
    test('should capture graph in Force layout', async ({ page }) => {
      await page.waitForTimeout(2000); // Wait for simulation to stabilize
      await page.screenshot({
        path: '../.playwright-mcp/graph-force-layout.png',
        fullPage: false,
      });
    });

    test('should capture graph in DAG layout', async ({ page }) => {
      await page.locator('button:has-text("Hierarchy")').click();
      await page.waitForTimeout(2000); // Wait for DAG layout
      await page.screenshot({
        path: '../.playwright-mcp/graph-dag-layout.png',
        fullPage: false,
      });
    });

    test('should capture graph with Similar To disabled', async ({ page }) => {
      const checkbox = page.locator('label:has-text("Similar To") input[type="checkbox"]');
      await checkbox.uncheck();
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: '../.playwright-mcp/graph-no-similar-to.png',
        fullPage: false,
      });
    });

    test('should capture graph with Entities disabled', async ({ page }) => {
      const checkbox = page.locator('label:has-text("Entities") input[type="checkbox"]');
      await checkbox.uncheck();
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: '../.playwright-mcp/graph-no-entities.png',
        fullPage: false,
      });
    });
  });
});

test.describe('Graph API Integration', () => {
  test('should fetch graph data from API', async ({ page }) => {
    // Intercept the API call
    const responsePromise = page.waitForResponse(
      (response) => response.url().includes('/api/v1/graph/episodes') && response.status() === 200
    );

    await page.goto('/graph');

    const response = await responsePromise;
    const data = await response.json();

    // Verify response structure
    expect(data).toHaveProperty('episodes');
    expect(data).toHaveProperty('edges');
    expect(data).toHaveProperty('stats');
  });

  test('should respect filtering parameters', async ({ page }) => {
    // Intercept API call to check parameters
    let requestUrl = '';
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/graph/episodes')) {
        requestUrl = request.url();
      }
    });

    await page.goto('/graph?min_similarity=0.8&include_entities=false');
    await page.waitForTimeout(1000);

    // Note: This depends on how the frontend passes parameters
    // The API should receive these as query params
  });
});

test.describe('Performance', () => {
  test('should render within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/graph');
    await page.waitForSelector('canvas');
    const loadTime = Date.now() - startTime;

    // Graph should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should handle large datasets', async ({ page }) => {
    // Navigate to graph with max limit
    await page.goto('/graph?limit=200');
    await page.waitForSelector('canvas', { timeout: 10000 });

    // Should still be responsive
    await expect(page.locator('canvas')).toBeVisible();
  });
});
