import { FileText } from 'lucide-react';
import InfoPageLayout, { InfoSection } from './InfoPageLayout';

export default function TermsAndConditionsPage() {
  return (
    <InfoPageLayout title="Terms & Conditions" description="The basic rules for using RentCoPartner." icon={FileText}>
      <InfoSection title="Your account">Provide accurate account and profile information, keep your login details secure, and use only an account you are authorized to access. You are responsible for activity under your account.</InfoSection>
      <InfoSection title="Using the service">Use RentCoPartner lawfully and respectfully. Do not mislead other users, harass anyone, interfere with the service, or use another person’s personal information without permission.</InfoSection>
      <InfoSection title="Bookings and payments">Review the service, timing, price, and cancellation details shown for a booking before you confirm it. A booking is subject to the details displayed in the app and any confirmation provided for that booking.</InfoSection>
      <InfoSection title="Profiles and interactions">Users are responsible for their own decisions and interactions. Keep communication respectful and report concerns through the available support route.</InfoSection>
      <InfoSection title="Changes and availability">Features may change as the service develops. We may restrict access where needed to protect users or the service, subject to applicable law.</InfoSection>
    </InfoPageLayout>
  );
}
