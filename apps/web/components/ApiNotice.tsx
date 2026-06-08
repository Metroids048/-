export function ApiNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  if (!message) return null;

  return (
    <div className="api-notice" role="status">
      <div>
        <strong>接口状态</strong>
        <p>{message}</p>
      </div>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          重试
        </button>
      ) : null}
    </div>
  );
}
