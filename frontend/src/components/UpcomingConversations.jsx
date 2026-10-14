import { useState } from "react";
import { ArrowRight } from "lucide-react";
import ConversationCard from "./ConversationCard.jsx";
import { conversationFilters, conversations } from "../data/home.js";
import "./UpcomingConversations.css";

export default function UpcomingConversations() {
  const [active, setActive] = useState("All");

  const visible =
    active === "All"
      ? conversations.slice(0, 3)
      : conversations.filter((c) => c.category === active);

  return (
    <section className="upcoming section" id="conversations">
      <div className="container">
        <div className="upcoming__head">
          <div>
            <p className="eyebrow">Upcoming conversation</p>
            <h2 className="section-title upcoming__title">
              Join a room that fits your Business
            </h2>
          </div>
          <a href="#conversations" className="link-more">
            All Conversations <ArrowRight size={16} strokeWidth={2.4} />
          </a>
        </div>

        <div className="upcoming__filters">
          {conversationFilters.map((filter) => (
            <button
              key={filter}
              type="button"
              className={`pill${active === filter ? " pill--active" : ""}`}
              onClick={() => setActive(filter)}
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="upcoming__grid">
          {visible.length > 0 ? (
            visible.map((conversation) => (
              <ConversationCard key={conversation.id} conversation={conversation} />
            ))
          ) : (
            <p className="upcoming__empty">
              No upcoming conversations in this category yet.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
