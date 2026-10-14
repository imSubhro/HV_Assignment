import { ArrowRight, CalendarDays, CheckCircle2, Video } from "lucide-react";
import Avatar from "./ui/Avatar.jsx";
import AvatarStack from "./ui/AvatarStack.jsx";
import Photo from "./ui/Photo.jsx";
import { heroAvatars, heroCard, heroImage } from "../data/home.js";
import "./Hero.css";

export default function Hero() {
  return (
    <section className="hero">
      <div className="container hero__inner">
        <div className="hero__left">
          <div className="hero__proof">
            <AvatarStack avatars={heroAvatars} size={30} />
            <span className="hero__proof-text">
              <strong>10+</strong> Founders already in the room
            </span>
          </div>

          <p className="eyebrow hero__eyebrow">
            A curated community for founders and business leaders
          </p>

          <h1 className="hero__title">
            Build Better Businesses through better <span>conversation</span>.
          </h1>

          <p className="hero__desc">
            Meet founders, CEOs and business leaders. Exchange ideas, solve real
            challenges, and build meaningful connections that go beyond the
            session.
          </p>

          <div className="hero__buttons">
            <a href="#join" className="btn btn--outline">
              Join the Community <ArrowRight size={15} strokeWidth={2.4} />
            </a>
            <a href="#conversations" className="btn btn--outline">
              Explore Conversations
            </a>
          </div>
        </div>

        <div className="hero__right">
          <div className="hero__image-wrap">
            <Photo
              src={heroImage}
              alt="Founders in conversation at a community session"
              className="hero__image"
            />

            <div className="hero-card hero-card--next">
              <div className="hero-card__head">
                <span className="hero-card__label">
                  <CalendarDays size={13} strokeWidth={2.2} />
                  {heroCard.label}
                </span>
                <span className="hero-card__when">{heroCard.when}</span>
              </div>
              <h3 className="hero-card__title">{heroCard.title}</h3>
              <div className="hero-card__meta">
                <AvatarStack avatars={heroCard.avatars} size={22} />
                <span>
                  {heroCard.founders}
                  <i> • </i>
                  {heroCard.duration}
                </span>
              </div>
              <div className="hero-card__tags">
                {heroCard.tags.map((tag) => (
                  <span key={tag} className="hero-card__tag">
                    {tag}
                  </span>
                ))}
                <span className="circle-btn circle-btn--gold hero-card__arrow">
                  <ArrowRight size={15} strokeWidth={2.4} />
                </span>
              </div>
            </div>

            <div className="hero-pill">
              <Video size={15} strokeWidth={2.2} />
              Online Via Google Meet
            </div>

            <div className="hero-card hero-card--done">
              <span className="hero-card__label">
                <CheckCircle2 size={13} strokeWidth={2.2} />
                Conversation complete
              </span>
              <h3 className="hero-card__title">8 participants connected</h3>
              <AvatarStack
                avatars={heroCard.avatars}
                extra={4}
                size={24}
                className="hero-card__done-avatars"
              />
              <ul className="hero-card__checks">
                <li>
                  <CheckCircle2 size={14} strokeWidth={2.2} />
                  Exchange contact details
                </li>
                <li>
                  <CheckCircle2 size={14} strokeWidth={2.2} />
                  Continue the conversation
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
