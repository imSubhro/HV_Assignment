import Avatar from "./Avatar.jsx";

/**
 * Overlapping avatar row with an optional "+N" chip.
 */
export default function AvatarStack({ avatars = [], extra = 0, size = 28 }) {
  return (
    <div className="avatar-stack" style={{ "--avatar-size": `${size}px` }}>
      {avatars.map((src, index) => (
        <Avatar
          key={index}
          src={src}
          name={`Member ${index + 1}`}
          size={size}
          className="avatar-stack__item"
        />
      ))}
      {extra > 0 && (
        <span className="avatar-stack__extra" style={{ width: size, height: size }}>
          +{extra}
        </span>
      )}
    </div>
  );
}
