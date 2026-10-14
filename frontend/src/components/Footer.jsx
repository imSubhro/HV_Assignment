import { ArrowRight, Linkedin, Mail, Twitter } from "lucide-react";
import { footerColumns, navLinks } from "../data/home.js";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__top">
          <div className="footer__brand">
            <span className="footer__logo">[Community Name]</span>
            <p className="footer__tagline">
              A curated community where founders and business leaders meet,
              exchange ideas, and keep the conversation going after the session.
            </p>
            <a href="#join" className="link-more link-more--light footer__link">
              Join the Community <ArrowRight size={16} strokeWidth={2.4} />
            </a>
            <div className="footer__social">
              <a href="#twitter" className="footer__icon" aria-label="Twitter">
                <Twitter size={16} strokeWidth={2.1} />
              </a>
              <a href="#linkedin" className="footer__icon" aria-label="LinkedIn">
                <Linkedin size={16} strokeWidth={2.1} />
              </a>
              <a href="#mail" className="footer__icon" aria-label="Email">
                <Mail size={16} strokeWidth={2.1} />
              </a>
            </div>
          </div>

          {footerColumns.map((column) => (
            <nav key={column.title} className="footer__col">
              <h4 className="footer__heading">{column.title}</h4>
              <ul>
                {column.links.map((link) => (
                  <li key={link}>
                    <a href="#">{link}</a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}

          <nav className="footer__col">
            <h4 className="footer__heading">Company</h4>
            <ul>
              {navLinks.map((link) => (
                <li key={link.label}>
                  <a href={link.href}>{link.label}</a>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="footer__bottom">
          <span>© 2026 [Community Name]. All rights reserved.</span>
          <div className="footer__legal">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
