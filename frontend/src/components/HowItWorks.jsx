import { BarChart3, CalendarDays, Hand, MessageSquare, ThumbsUp, Video } from "lucide-react";
import Avatar from "./ui/Avatar.jsx";
import AvatarStack from "./ui/AvatarStack.jsx";
import Photo from "./ui/Photo.jsx";
import ConversationCard from "./ConversationCard.jsx";
import { confirmSpots, conversations, newConnections, steps } from "../data/home.js";
import "./HowItWorks.css";

function ConfirmSpotsCard() {
  return (
    <div className="hiw-card hiw-card--confirm">
      <h4 className="hiw-card__title">Confirm your Spots</h4>
      <p className="hiw-card__row">
        <CalendarDays size={14} strokeWidth={2.1} />
        <span>
          {confirmSpots.date}
          <br />
          {confirmSpots.time}
        </span>
      </p>
      <p className="hiw-card__row">
        <Video size={14} strokeWidth={2.1} />
        <span>{confirmSpots.mode}</span>
      </p>
      <div className="hiw-card__joining">
        <AvatarStack avatars={confirmSpots.avatars} size={22} />
        <span>{confirmSpots.joining}</span>
      </div>
      <button type="button" className="btn btn--dark btn--sm hiw-card__cta">
        Register Now
      </button>
    </div>
  );
}

function SessionCard() {
  return (
    <div className="hiw-session">
      <Photo
        src={conversations[2].image}
        alt="Live session in progress"
        className="hiw-session__img"
      />
      <span className="hiw-session__pill">
        <Video size={12} strokeWidth={2.2} />
        Online Via Google Meet
      </span>
      <div className="hiw-session__bar">
        <span>
          <Hand size={15} strokeWidth={2.1} />
          Ask
        </span>
        <span>
          <ThumbsUp size={15} strokeWidth={2.1} />
          Vote
        </span>
        <span>
          <MessageSquare size={15} strokeWidth={2.1} />
          Discuss
        </span>
      </div>
    </div>
  );
}

function ConnectionsCard() {
  return (
    <div className="hiw-card hiw-card--connections">
      <h4 className="hiw-card__title">New Connections</h4>
      <ul className="hiw-connections">
        {newConnections.map((person) => (
          <li key={person.name}>
            <Avatar src={person.avatar} name={person.name} size={34} />
            <div>
              <strong>{person.name}</strong>
              <span>{person.role}</span>
            </div>
            <span className="circle-btn circle-btn--gold hiw-connections__add">+</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function GrowNetwork() {
  return (
    <div className="hiw-network" aria-hidden="true">
      <span className="hiw-network__ring hiw-network__ring--1" />
      <span className="hiw-network__ring hiw-network__ring--2" />
      <span className="hiw-network__core">
        <BarChart3 size={22} strokeWidth={2.1} />
      </span>
      <Avatar
        src="https://i.pravatar.cc/80?img=12"
        className="hiw-network__node hiw-network__node--1"
        size={38}
      />
      <Avatar
        src="https://i.pravatar.cc/80?img=32"
        className="hiw-network__node hiw-network__node--2"
        size={38}
      />
      <Avatar
        src="https://i.pravatar.cc/80?img=45"
        className="hiw-network__node hiw-network__node--3"
        size={38}
      />
      <Avatar
        src="https://i.pravatar.cc/80?img=5"
        className="hiw-network__node hiw-network__node--4"
        size={38}
      />
    </div>
  );
}

function StepVisual({ index }) {
  if (index === 0) return <ConversationCard conversation={conversations[1]} mini />;
  if (index === 1) return <ConfirmSpotsCard />;
  if (index === 2) return <SessionCard />;
  if (index === 3) return <ConnectionsCard />;
  return <GrowNetwork />;
}

export default function HowItWorks() {
  return (
    <section className="hiw section" id="how-it-works">
      <div className="container">
        <p className="eyebrow">How it works</p>
        <h2 className="section-title hiw__title">
          Discover. Join. Participate. Connect. Grow.
        </h2>
        <p className="section-sub hiw__sub">
          A simple way to meet like-minded Founders, Business Leaders and
          Industry experts through meaningful conversations.
        </p>

        <div className="hiw__track">
          <svg
            className="hiw__lines"
            viewBox="0 0 1160 320"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="arrow-gold"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <path d="M0,0 L8,4 L0,8 Z" fill="#c29a61" />
              </marker>
            </defs>
            <path
              d="M200 120 C 240 190, 260 210, 330 235"
              fill="none"
              stroke="#d9b98a"
              strokeWidth="1.6"
              strokeDasharray="5 6"
              markerEnd="url(#arrow-gold)"
            />
            <path
              d="M520 250 C 560 200, 570 170, 640 145"
              fill="none"
              stroke="#d9b98a"
              strokeWidth="1.6"
              strokeDasharray="5 6"
              markerEnd="url(#arrow-gold)"
            />
            <path
              d="M820 120 C 860 170, 880 200, 950 225"
              fill="none"
              stroke="#d9b98a"
              strokeWidth="1.6"
              strokeDasharray="5 6"
              markerEnd="url(#arrow-gold)"
            />
          </svg>

          <div className="hiw__grid">
            {steps.map((step, index) => (
              <article
                key={step.num}
                className={`hiw__step${index % 2 === 1 ? " hiw__step--down" : ""}`}
              >
                <div className="hiw__head">
                  <span className="hiw__num">{step.num}</span>
                  <div>
                    <h3 className="hiw__step-title">{step.title}</h3>
                    <p className="hiw__step-text">{step.text}</p>
                  </div>
                </div>
                <div className="hiw__visual">
                  <StepVisual index={index} />
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
