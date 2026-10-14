import { ArrowRight } from "lucide-react";
import Avatar from "./ui/Avatar.jsx";
import { ctaAvatars } from "../data/home.js";
import "./CtaSection.css";

export default function CtaSection() {
  return (
    <section className="cta" id="join">
      <svg
        className="cta__path"
        viewBox="0 0 1440 420"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M-40 300 C 220 140, 420 420, 700 250 S 1180 90, 1500 240"
          fill="none"
          stroke="#d9b98a"
          strokeWidth="2"
          strokeDasharray="8 10"
        />
      </svg>

      {ctaAvatars.map((avatar) => (
        <Avatar
          key={avatar.className}
          src={avatar.src}
          className={avatar.className}
          size={54}
        />
      ))}

      <div className="container cta__inner">
        <p className="eyebrow">Ready when you are</p>
        <h2 className="cta__title">
          Your next great business conversation
          <br />
          starts here.
        </h2>
        <p className="cta__text">
          Join a curated community of founders and business leaders. Register
          for a conversation, share your experience, and keep the discussion
          going after the session.
        </p>
        <div className="cta__actions">
          <a href="#join" className="btn btn--dark">
            Join the Community <ArrowRight size={15} strokeWidth={2.4} />
          </a>
          <a href="#conversations" className="btn btn--outline">
            Explore Conversations
          </a>
        </div>
      </div>
    </section>
  );
}
