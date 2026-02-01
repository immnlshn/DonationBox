import { useEffect } from "react";

/**
 * Generic Popup Component for display-only website
 * Auto-closes after specified time - no interactive handlers needed
 */
export default function Popup({
  isOpen,
  onClose,
  autoCloseMs,
  type = "info",
  children
}) {
  // Auto-close timer (only way to close popup)
  useEffect(() => {
    if (!isOpen || !autoCloseMs) return;

    const timer = setTimeout(() => {
      onClose?.();
    }, autoCloseMs);

    return () => clearTimeout(timer);
  }, [isOpen, autoCloseMs, onClose]);

  if (!isOpen) return null;

  return (
    <div className="popup-overlay">
      <div className={`popup-container popup-${type}`}>
        {children}
      </div>
    </div>
  );
}
