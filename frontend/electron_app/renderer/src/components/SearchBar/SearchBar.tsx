import React from "react";

interface SearchBarProps {
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  placeholder = "Search...",
  onChange,
}) => {
  return (
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width: "100%",
        padding: "10px 12px",
        marginBottom: "12px",
        borderRadius: "8px",
        border: "1px solid #d1d5db",
        fontSize: "14px",
        outline: "none",
      }}
    />
  );
};

export default SearchBar;