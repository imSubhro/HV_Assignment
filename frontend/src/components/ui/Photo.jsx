import { useState } from "react";

/**
 * Photo with a soft gradient fallback when the remote image is unavailable.
 */
export default function Photo({ src, alt = "", className = "" }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return <div className={`photo photo--fallback ${className}`} role="img" aria-label={alt} />;
  }

  return (
    <img
      className={`photo ${className}`}
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
