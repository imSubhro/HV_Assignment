import { useState } from "react";

/**
 * Avatar image with graceful initials fallback if the URL fails to load.
 */
export default function Avatar({ src, name = "", size = 32, className = "" }) {
  const [failed, setFailed] = useState(false);
  const initials = name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (failed || !src) {
    return (
      <span
        className={`avatar avatar--fallback ${className}`}
        style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
        aria-label={name}
      >
        {initials || "?"}
      </span>
    );
  }

  return (
    <img
      className={`avatar ${className}`}
      style={{ width: size, height: size }}
      src={src}
      alt={name}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
