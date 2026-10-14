import { ArrowRight } from "lucide-react";
import { navLinks } from "../data/home.js";
import "./Navbar.css";

export default function Navbar() {
  return (
    <header className="nav">
      <div className="container nav__inner">
        <a href="#" className="nav__logo">
          [Community Name]
        </a>

        <nav className="nav__links" aria-label="Primary">
          {navLinks.map((link) => (
            <a key={link.label} href={link.href} className="nav__link">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="nav__actions">
          <a href="#signin" className="nav__signin">
            Sign in
          </a>
          <a href="#join" className="btn btn--dark btn--sm nav__cta">
            Join the Community <ArrowRight size={15} strokeWidth={2.4} />
          </a>
        </div>
      </div>
    </header>
  );
}
