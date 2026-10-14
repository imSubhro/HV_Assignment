import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import ValueProposition from "./components/ValueProposition.jsx";
import UpcomingConversations from "./components/UpcomingConversations.jsx";
import HowItWorks from "./components/HowItWorks.jsx";
import CommunityPreview from "./components/CommunityPreview.jsx";
import CtaSection from "./components/CtaSection.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <ValueProposition />
        <UpcomingConversations />
        <HowItWorks />
        <CommunityPreview />
        <CtaSection />
      </main>
      <Footer />
    </>
  );
}
