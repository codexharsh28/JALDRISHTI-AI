import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('JALDRISHTI AI ErrorBoundary caught an unhandled UI error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-950/40 border border-red-800 rounded-lg text-red-200 my-4 max-w-4xl mx-auto">
          <h2 className="text-xl font-bold mb-2 flex items-center gap-2 text-red-400">
            <span>⚠️</span> {this.props.fallbackTitle || 'Component Error Detected'}
          </h2>
          <p className="text-sm mb-4 opacity-90">
            A non-critical rendering error occurred in this view. The system operational telemetry remain safe.
          </p>
          <div className="bg-black/60 p-3 rounded text-xs font-mono overflow-x-auto text-red-300 border border-red-900/50">
            {this.state.error?.toString() || 'Unknown error'}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 bg-red-800 hover:bg-red-700 text-white rounded text-sm transition-colors font-medium"
          >
            Retry Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
