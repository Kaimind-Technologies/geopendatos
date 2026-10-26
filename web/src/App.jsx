import { I18nProvider } from "./i18n";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Problem from "./components/Problem";
import Progress from "./components/Progress";
import Mission from "./components/Mission";
import Method from "./components/Method";
import Roadmap from "./components/Roadmap";
import Discarded from "./components/Discarded";
import Api from "./components/Api";
import OpenSource from "./components/OpenSource";
import Footer from "./components/Footer";

export default function App({ lang }) {
  return (
    <I18nProvider lang={lang}>
      <Header />
      <main>
        <Hero />
        <Problem />
        <Progress />
        <Mission />
        <Method />
        <Discarded />
        <Api />
        <Roadmap />
        <OpenSource />
      </main>
      <Footer />
    </I18nProvider>
  );
}
