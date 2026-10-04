import { RotateCcw } from 'lucide-react';
import InfoPageLayout, { InfoSection } from './InfoPageLayout';

export default function RefundPolicyPage() {
  return (
    <InfoPageLayout title="Refund Policy" description="What to check when a booking is cancelled or does not go as planned." icon={RotateCcw}>
      <InfoSection title="Before confirming">Check the cancellation and refund details shown with the booking before you confirm. Those booking-specific details apply to that request.</InfoSection>
      <InfoSection title="Requesting help">If a booking is cancelled, duplicated, or charged incorrectly, open the booking in your account and contact support with its reference and a short description of the issue. Do not send full card or bank credentials.</InfoSection>
      <InfoSection title="Review">Refund requests are reviewed against the booking status, payment record, and the terms shown when the booking was made. If approved, the return is sent through the original payment method where available; the payment provider may control when it appears.</InfoSection>
      <InfoSection title="Need assistance?">Visit Help for account and booking links. Keep your booking reference so the issue can be identified.</InfoSection>
    </InfoPageLayout>
  );
}
