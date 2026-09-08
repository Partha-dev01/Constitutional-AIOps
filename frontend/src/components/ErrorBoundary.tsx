import { Component, ErrorInfo, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, RefreshCw, LayoutDashboard } from 'lucide-react'

interface ErrorBoundaryProps {
  children: ReactNode
  /**
   * When this value changes the boundary resets its error state. Pass the
   * current route (e.g. location.pathname) so navigating away from a crashed
   * page recovers automatically instead of showing the fallback forever.
   */
  resetKey?: string | number
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Catches render/lifecycle errors in its subtree and shows an on-theme
 * fallback card instead of unmounting the whole SPA to a blank screen.
 *
 * Class component because getDerivedStateFromError / componentDidCatch have no
 * hooks equivalent.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface the error + component stack for debugging.
    console.error('ErrorBoundary caught an error:', error, info.componentStack)
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // Reset the error state when the reset key changes (e.g. route change), so
    // navigating away from a crashed route restores the subtree.
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false, error: null })
    }
  }

  private handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <div className="flex items-center justify-center p-6">
        <div className="bg-card border border-border text-foreground rounded-lg p-6 max-w-lg w-full shadow-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-500 shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold">Something went wrong</h2>
              <p className="text-sm text-muted-foreground mt-1">
                This view hit an unexpected error and couldn&apos;t be displayed. You can reload
                the page or head back to the dashboard.
              </p>
              {this.state.error?.message && (
                <p className="mt-3 text-xs font-mono text-muted-foreground wrap-break-word bg-muted/50 rounded-sm p-2">
                  {this.state.error.message}
                </p>
              )}
            </div>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <button
              onClick={this.handleReload}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
            >
              <RefreshCw className="h-4 w-4" />
              Reload
            </button>
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80"
            >
              <LayoutDashboard className="h-4 w-4" />
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    )
  }
}

export default ErrorBoundary
