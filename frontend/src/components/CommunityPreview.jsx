import { ArrowRight } from "lucide-react";
import Photo from "./ui/Photo.jsx";
import { members } from "../data/home.js";
import "./CommunityPreview.css";

export default function CommunityPreview() {
  return (
    <section className="community section" id="community">
      <div className="container">
        <div className="community__head">
          <div>
            <p className="eyebrow">Community preview</p>
            <h2 className="section-title community__title">Who you&rsquo;ll meet</h2>
            <p className="section-sub">
              Founders, CEOs and Industry Experts from diverse backgrounds,
              coming together to share real experiences and practical insights.
            </p>
          </div>
          <a href="#community" className="link-more">
            Meet the Community <ArrowRight size={16} strokeWidth={2.4} />
          </a>
        </div>

        <div className="community__grid">
          {members.map((member) => (
            <article key={member.name} className="member">
              <div className="member__photo-wrap">
                <Photo
                  src={member.photo}
                  alt={member.name}
                  className="member__photo"
                />
              </div>
              <div className="member__row">
                <div>
                  <h3 className="member__name">{member.name}</h3>
                  <p className="member__role">{member.role}</p>
                </div>
                <span className="circle-btn circle-btn--gold">
                  <ArrowRight size={15} strokeWidth={2.4} />
                </span>
              </div>
              <div className="member__tags">
                {member.tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
