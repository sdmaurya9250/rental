import MainContent from './MainContent';

function CategoryPage({ title, description }) {
  return (
    <div>
      <div className="border-b border-[#e7e1f2] bg-white px-6 py-5 lg:px-8">
        <h1 className="text-2xl font-bold text-[#171426]">{title}</h1>
        <p className="mt-1 text-sm text-[#706a80]">{description}</p>
      </div>
      <MainContent />
    </div>
  );
}

export const DateCompanionPage = () => <CategoryPage title="Date companions" description="Browse people for dinners, social occasions, and quality time." />;
export const TravelBuddyPage = () => <CategoryPage title="Travel buddies" description="Find a companion for your next journey." />;
export const EventPartnerPage = () => <CategoryPage title="Event partners" description="Meet people for parties, concerts, and special events." />;
export const ConversationPage = () => <CategoryPage title="Conversation partners" description="Find someone to talk with and share a good conversation." />;
export const FitnessPage = () => <CategoryPage title="Fitness buddies" description="Stay motivated with a fitness companion." />;
export const NetworkingPage = () => <CategoryPage title="Professional networking" description="Connect with people for work and professional events." />;
export const PhotoshootPage = () => <CategoryPage title="Photoshoot partners" description="Find a partner for your next creative shoot." />;
export const GamingPage = () => <CategoryPage title="Gaming buddies" description="Play together and discover new games." />;
export const OtherPage = () => <CategoryPage title="Other activities" description="Explore people for more shared activities." />;
