import { ShieldCheck } from 'lucide-react';
import InfoPageLayout, { InfoSection } from './InfoPageLayout';

export default function PrivacyPolicyPage() {
  return (
    <InfoPageLayout title="Privacy Policy" description="How RentCoPartner handles information you choose to share." icon={ShieldCheck}>
      <InfoSection title="Information you provide">When you create an account, we receive details such as your name, email, phone number, city, pincode, gender, account preferences, and profile information. The service also stores information needed to provide bookings and messaging.</InfoSection>
      <InfoSection title="Location">If you choose Detect my location and allow browser access, your city and device coordinates are sent with your registration so your profile can be found by location. You can also enter a city manually. You can change location details from your profile.</InfoSection>
      <InfoSection title="How information is used">Information is used to operate your account, show relevant profiles, support bookings and messages, and protect the service. We do not ask for precise location unless you choose the location detection control.</InfoSection>
      <InfoSection title="Account security and choices">Keep your password private. You can update profile information in the app. Browser location access can be changed in your browser’s site settings at any time.</InfoSection>
      <InfoSection title="Questions">For privacy questions, use the Help page and include the account email and a description of your request.</InfoSection>
    </InfoPageLayout>
  );
}
