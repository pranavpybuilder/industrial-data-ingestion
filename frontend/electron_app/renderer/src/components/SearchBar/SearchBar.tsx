import React, { useState, useRef, useEffect } from "react";
import { FiSearch, FiX } from "react-icons/fi";

interface SearchBarProps {
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
  /** Compact mode for modals / tight layouts */
  compact?: boolean;
  /** Show Ctrl+K keyboard shortcut hint */
  showShortcut?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  placeholder = "Search...",
  onChange,
  compact = false,
  showShortcut = false,
}) => {
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global Ctrl+K shortcut
  useEffect(() => {
    if (!showShortcut) return;
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [showShortcut]);

  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        width: "100%",
        marginBottom: compact ? "0" : "12px",
      }}
    >
      {/* Search icon */}
      <FiSearch
        size={16}
        style={{
          position: "absolute",
          left: "12px",
          color: focused ? "#6366f1" : "#9ca3af",
          transition: "color 0.15s ease",
          pointerEvents: "none",
        }}
      />

      {/* Input */}
      <input
        ref={inputRef}
        type="text"
        value={value}
        placeholder={placeholder}
        aria-label={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          width: "100%",
          padding: compact ? "9px 36px 9px 36px" : "11px 80px 11px 38px",
          borderRadius: "10px",
          border: `1.5px solid ${focused ? "#6366f1" : "#e5e7eb"}`,
          fontSize: "14px",
          outline: "none",
          background: focused ? "#ffffff" : "#f9fafb",
          color: "#111827",
          transition: "all 0.2s ease",
          boxShadow: focused
            ? "0 0 0 3px rgba(99, 102, 241, 0.12), 0 2px 8px rgba(0,0,0,0.06)"
            : "0 1px 2px rgba(0,0,0,0.04)",
        }}
      />

      {/* Clear button */}
      {value && (
        <button
          onClick={() => onChange("")}
          style={{
            position: "absolute",
            right: showShortcut ? "56px" : "10px",
            background: "none",
            border: "none",
            color: "#9ca3af",
            cursor: "pointer",
            padding: "4px",
            display: "flex",
            alignItems: "center",
            borderRadius: "4px",
            transition: "color 0.15s ease",
          }}
          title="Clear search"
        >
          <FiX size={15} />
        </button>
      )}

      {/* Keyboard shortcut badge */}
      {showShortcut && !value && !focused && (
        <div
          style={{
            position: "absolute",
            right: "10px",
            display: "flex",
            alignItems: "center",
            gap: "2px",
            pointerEvents: "none",
          }}
        >
          <kbd
            style={{
              fontSize: "11px",
              fontFamily: "inherit",
              color: "#9ca3af",
              background: "#f3f4f6",
              border: "1px solid #e5e7eb",
              borderRadius: "4px",
              padding: "2px 5px",
              lineHeight: 1,
            }}
          >
            Ctrl
          </kbd>
          <kbd
            style={{
              fontSize: "11px",
              fontFamily: "inherit",
              color: "#9ca3af",
              background: "#f3f4f6",
              border: "1px solid #e5e7eb",
              borderRadius: "4px",
              padding: "2px 5px",
              lineHeight: 1,
            }}
          >
            K
          </kbd>
        </div>
      )}
    </div>
  );
};

export default SearchBar;