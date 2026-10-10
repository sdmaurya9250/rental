import { ShieldCheck } from 'lucide-react';
import InfoPageLayout, { InfoSection } from './InfoPageLayout';
import Seo from '../components/Seo';

export default function PrivacyPolicyPage() {
  return (
    <>
    <Seo title="Privacy Policy | RentCoPartner" description="Read how RentCoPartner collects, uses, stores and protects information you provide when using our website, accounts and companion booking services." />
    <InfoPageLayout
      title="Privacy Policy"
      description="How RentCoPartner collects, uses, and protects your information."
      icon={ShieldCheck}
    >
      <InfoSection title="Last Updated">
        October 2026
      </InfoSection>

      <InfoSection title="1. About this Privacy Policy">
        RentCoPartner ("we", "us", "our", or "the Platform") respects your
        privacy and is committed to protecting the personal information you
        choose to provide when using our website, services, and related
        features.

        This Privacy Policy explains what information we collect, how we use
        it, how it may be shared, and the choices available to you.
      </InfoSection>

      <InfoSection title="2. Information You Provide">
        When you create an account or use RentCoPartner, we may collect
        information such as your name, email address, mobile number, city,
        pincode, gender, date of birth or age information where required,
        profile photograph, profile description, preferences, and other
        information you choose to add to your profile.

        We may also collect information related to your bookings, favourites,
        messages, requests, and interactions with other users on the Platform.
      </InfoSection>

      <InfoSection title="3. Location Information">
        RentCoPartner may allow you to provide your location so that profiles
        and services can be displayed based on your selected area.

        If you use a "Detect my location" or similar feature and provide
        browser permission, your device may provide location information,
        including approximate or precise coordinates depending on your
        browser and device settings.

        You may also enter your city, pincode, or location manually instead
        of using device-based location detection.

        You can control or disable browser location permissions through your
        device or browser settings.
      </InfoSection>

      <InfoSection title="4. Information Collected Automatically">
        When you access RentCoPartner, certain technical information may be
        collected automatically, such as your IP address, browser type,
        operating system, device information, pages visited, approximate
        location, and information about how you interact with the Platform.

        This information may be used to maintain security, improve performance,
        understand usage, and provide a better user experience.
      </InfoSection>

      <InfoSection title="5. How We Use Your Information">
        We may use your information to:

        • Create and manage your RentCoPartner account.
        • Display your profile to relevant users.
        • Help users discover partners based on selected location and
        preferences.
        • Facilitate bookings, requests, favourites, and communications.
        • Provide customer support and respond to enquiries.
        • Send important account, booking, and service notifications.
        • Protect the Platform against fraud, misuse, spam, and unauthorized
        activity.
        • Improve our website, features, and user experience.
        • Comply with applicable laws and legal requirements.
      </InfoSection>

      <InfoSection title="6. Profile and Public Information">
        Depending on the features you use and your account settings, certain
        information from your profile may be visible to other users.

        This may include your name or display name, profile photograph,
        description, city, pincode or service area, preferences, and other
        information you voluntarily publish.

        Please avoid posting sensitive personal information publicly in your
        profile, photographs, messages, or descriptions.
      </InfoSection>

      <InfoSection title="7. Bookings, Messages and Favourites">
        Information associated with bookings, requests, favourites, and
        messages may be stored so that RentCoPartner can provide these
        features, maintain account history, resolve disputes, prevent abuse,
        and improve the Platform.

        You should only share information with other users that you are
        comfortable sharing.
      </InfoSection>

      <InfoSection title="8. Payments">
        If RentCoPartner provides payment or booking-payment functionality,
        payment transactions may be processed through third-party payment
        service providers.

        RentCoPartner does not intentionally request or store your payment
        authentication information such as UPI PIN, ATM PIN, CVV, or banking
        passwords.

        Payment providers may collect and process payment information in
        accordance with their own privacy policies and terms.
      </InfoSection>

      <InfoSection title="9. Cookies and Similar Technologies">
        RentCoPartner may use cookies, local storage, session technologies,
        and similar technologies to keep you signed in, remember preferences,
        maintain security, understand website usage, and improve the Platform.

        You can control cookies through your browser settings. Disabling
        certain cookies or browser storage may affect some Platform features.
      </InfoSection>

      <InfoSection title="10. Sharing of Information">
        We may share information when reasonably necessary to operate
        RentCoPartner, including with:

        • Service providers that help us host, maintain, secure, or operate
        the Platform.
        • Payment or transaction providers where applicable.
        • Other users when information is intentionally made visible through
        profiles, bookings, or Platform features.
        • Authorities, regulators, courts, or law-enforcement agencies when
        required by applicable law or valid legal process.

        We do not sell your personal information to third parties for their
        independent marketing purposes.
      </InfoSection>

      <InfoSection title="11. Data Security">
        We take reasonable technical and organizational measures designed to
        protect your information from unauthorized access, misuse, alteration,
        disclosure, or destruction.

        However, no website, application, database, or internet transmission
        can be guaranteed to be completely secure. You are responsible for
        keeping your account credentials confidential and should notify us if
        you believe your account has been accessed without authorization.
      </InfoSection>

      <InfoSection title="12. Data Retention">
        We retain information for as long as reasonably necessary to provide
        our services, maintain your account, comply with legal obligations,
        resolve disputes, prevent fraud and abuse, and enforce our agreements.

        When information is no longer required, we may delete, anonymize, or
        securely dispose of it, subject to applicable legal and operational
        requirements.
      </InfoSection>

      <InfoSection title="13. Your Choices and Rights">
        Depending on applicable law, you may have rights to request access to,
        correction of, or deletion of certain personal information.

        You may also update information through your account where the
        Platform provides editing functionality.

        You can withdraw browser location permission through your browser or
        device settings.

        For privacy-related requests, please contact RentCoPartner through
        the Help or Contact page and provide the email address associated with
        your account and a description of your request.
      </InfoSection>

      <InfoSection title="14. Children's Privacy">
        RentCoPartner is intended for users who are 18 years of age or older.

        We do not knowingly provide services to or intentionally collect
        personal information from individuals under 18. If we become aware
        that information has been collected from a person under 18, we may
        take reasonable steps to delete the information and restrict the
        associated account.
      </InfoSection>

      <InfoSection title="15. Third-Party Services">
        RentCoPartner may use third-party services for hosting, authentication,
        analytics, payments, communications, security, or other technical
        functions.

        These providers may process information according to their own
        privacy policies and applicable agreements.
      </InfoSection>

      <InfoSection title="16. Changes to this Privacy Policy">
        We may update this Privacy Policy from time to time to reflect changes
        to our Platform, services, technology, or legal requirements.

        When material changes are made, we may provide notice through the
        Platform or other appropriate means. The updated policy will become
        effective when published unless otherwise stated.
      </InfoSection>

      <InfoSection title="17. Contact Us">
        If you have questions, concerns, or requests relating to this Privacy
        Policy or your personal information, please contact us through the
        RentCoPartner Help or Contact page.

        Please include the email address associated with your account and
        clearly describe your request so that we can assist you efficiently.
      </InfoSection>
    </InfoPageLayout>
    </>
  );
}
