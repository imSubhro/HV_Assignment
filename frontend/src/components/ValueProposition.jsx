import { valueProps } from "../data/home.js";
import "./ValueProposition.css";

export default function ValueProposition() {
  return (
    <section className="vp">
      <div className="container">
        <p className="eyebrow eyebrow--dark vp__eyebrow">Value Proposition</p>
        <div className="vp__grid">
          {valueProps.map((item) => (
            <article key={item.num} className="vp__item">
              <div className="vp__num">
                <span className="vp__dash" />
                {item.num}
              </div>
              <h3 className="vp__title">{item.title}</h3>
              <p className="vp__text">{item.text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
