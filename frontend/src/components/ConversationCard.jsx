import { ArrowRight, CalendarDays, Clock, Users, Video } from "lucide-react";
import AvatarStack from "./ui/AvatarStack.jsx";
import Photo from "./ui/Photo.jsx";
import "./ConversationCard.css";

/**
 * Conversation card used in the "Upcoming conversation" grid
 * and (in mini form) inside the "How it works" section.
 */
export default function ConversationCard({ conversation, mini = false }) {
  return (
    <article className={`conv${mini ? " conv--mini" : ""}`}>
      <div className="conv__media">
        <Photo src={conversation.image} alt={conversation.title} className="conv__img" />
        <span className="conv__category">
          <i />
          {conversation.category}
        </span>
      </div>

      <div className="conv__body">
        <div className="conv__pills">
          <span className="conv__pill">
            <Users size={13} strokeWidth={2.2} />
            Only <b>{conversation.spotsLeft}</b> spots left
          </span>
          <span className="conv__pill">
            <Clock size={13} strokeWidth={2.2} />
            {conversation.duration} minutes
          </span>
        </div>

        <h3 className="conv__title">{conversation.title}</h3>

        <div className="conv__meta">
          <span>
            <CalendarDays size={13} strokeWidth={2.1} />
            {conversation.when}
          </span>
          <span>
            <Video size={13} strokeWidth={2.1} />
            {conversation.mode}
          </span>
        </div>

        <div className="conv__host">
          <AvatarStack avatars={conversation.speakers} extra={conversation.extra} size={26} />
          <div className="conv__host-text">
            <p>
              Hosted by <strong>{conversation.host}</strong>
            </p>
            <span>{conversation.hostRole}</span>
          </div>
        </div>

        <div className="conv__footer">
          <a href="#conversations" className="conv__link">
            View Conversation <ArrowRight size={14} strokeWidth={2.4} />
          </a>
          <span className="circle-btn conv__arrow">
            <ArrowRight size={16} strokeWidth={2.4} />
          </span>
        </div>
      </div>
    </article>
  );
}
