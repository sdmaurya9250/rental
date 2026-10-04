import { CircleHelp } from 'lucide-react';
import InfoPageLayout, { InfoSection } from './InfoPageLayout';

export default function HelpPage() {
  return (
    <InfoPageLayout title="Help Center" description="Quick answers for common account, location, and booking questions." icon={CircleHelp}>
      <InfoSection title="I can’t log in">Check that you are using the email and password registered to your account. If you are new, create an account from the registration page.</InfoSection>
      <InfoSection title="Location is blocked in Chrome">Choose the site controls icon beside the address bar, open Site settings, set Location to Allow, then return to registration and tap Detect my location again. You can enter your city manually instead.</InfoSection>
      <InfoSection title="How do I update my profile?">Sign in and open My profile to update your city, profile details, and availability.</InfoSection>
      <InfoSection title="Where are my bookings?">Sign in and open My bookings to review booking information and status. Check the Refund Policy for help with cancellations or payment issues.</InfoSection>
    </InfoPageLayout>
  );
}
