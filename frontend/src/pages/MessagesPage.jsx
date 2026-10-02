import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Send } from 'lucide-react';
import FeaturePage from '../components/FeaturePage';
import { getStoredUser, isAuthenticated } from '../auth/auth';
import { fetchConversationMessages, fetchConversations, sendChatMessage } from './finderApi';

function listFrom(result, key) {
  if (Array.isArray(result)) return result;
  return Array.isArray(result?.[key]) ? result[key] : [];
}

function conversationUserId(conversation) {
  return String(
    conversation.other_user_id || conversation.participant_id || conversation.user_id ||
    conversation.receiver_id || conversation.person_id || conversation.other_user?.id ||
    conversation.participant?.id || conversation.user?.id || conversation.id || '',
  );
}

function conversationName(conversation) {
  return conversation.other_user?.name || conversation.participant?.name || conversation.user?.name ||
    conversation.person_name || conversation.name || conversation.full_name || 'Conversation';
}

function personImage(person) {
  return person?.image || person?.profile_image || person?.avatar_url || person?.photo || person?.avatar || '';
}

function messageContent(message) {
  return message.content || message.message || message.text || '';
}

export default function MessagesPage() {
  const [searchParams] = useSearchParams();
  const requestedUserId = searchParams.get('userId') || '';
  const currentUser = getStoredUser();
  const currentUserId = String(currentUser?.id || currentUser?.user_id || currentUser?.profile_id || '');
  const [conversations, setConversations] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(requestedUserId);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [loadingInbox, setLoadingInbox] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    if (!isAuthenticated()) {
      setError('Sign in to view your messages.');
      setLoadingInbox(false);
      return () => { active = false; };
    }
    fetchConversations()
      .then((result) => {
        if (!active) return;
        const items = listFrom(result, 'conversations');
        setConversations(items);
        setSelectedUserId((selected) => selected || (items[0] ? conversationUserId(items[0]) : ''));
      })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load conversations.'); })
      .finally(() => { if (active) setLoadingInbox(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedUserId) {
      setMessages([]);
      return undefined;
    }
    let active = true;
    setLoadingMessages(true);
    fetchConversationMessages(selectedUserId)
      .then((result) => { if (active) setMessages(listFrom(result, 'messages')); })
      .catch((requestError) => { if (active) setError(requestError.message || 'Unable to load this conversation.'); })
      .finally(() => { if (active) setLoadingMessages(false); });
    return () => { active = false; };
  }, [selectedUserId]);

  const selectedConversation = useMemo(
    () => conversations.find((item) => conversationUserId(item) === selectedUserId),
    [conversations, selectedUserId],
  );
  const partner = selectedConversation?.other_user || selectedConversation?.participant || selectedConversation?.user || selectedConversation;
  const partnerName = selectedConversation ? conversationName(selectedConversation) : messages[0]?.sender?.name || messages[0]?.receiver?.name || 'Conversation';
  const partnerImage = personImage(partner) || personImage(messages[0]?.sender) || personImage(messages[0]?.receiver);
  const currentUserName = currentUser?.name || currentUser?.full_name || currentUser?.username || 'You';
  const currentUserImage = personImage(currentUser);

  async function submitMessage(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !selectedUserId || sending) return;
    setSending(true);
    setError('');
    try {
      const result = await sendChatMessage(selectedUserId, content);
      const sent = result?.message || result;
      setMessages((current) => [...current, {
        ...(sent && typeof sent === 'object' ? sent : {}),
        content: messageContent(sent) || content,
        sender_id: sent?.sender_id || currentUserId,
        is_mine: true,
      }]);
      setDraft('');
    } catch (requestError) {
      setError(requestError.message || 'Unable to send this message.');
    } finally {
      setSending(false);
    }
  }

  if (!isAuthenticated()) {
    return <FeaturePage title="Messages" subtitle="Finders and RentPeople can chat here."><p className="text-sm text-amber-700">{error} <Link to="/login" className="font-semibold underline">Sign in</Link></p></FeaturePage>;
  }

  return (
    <FeaturePage title="Messages" subtitle="Finders and RentPeople can chat with each other here.">
      <div className="grid max-w-5xl overflow-hidden rounded-2xl border border-[#e7e1f2] bg-white shadow-sm md:grid-cols-[280px_1fr]">
        <aside className="border-b border-[#eeeaf5] md:border-b-0 md:border-r">
          <h2 className="border-b border-[#eeeaf5] px-4 py-3 text-sm font-bold">Conversations</h2>
          {loadingInbox ? <p className="p-4 text-sm text-[#706a80]">Loading conversations…</p> : conversations.length === 0 ? (
            <p className="p-4 text-sm text-[#706a80]">No conversations yet.</p>
          ) : conversations.map((conversation, index) => {
            const userId = conversationUserId(conversation);
            const name = conversationName(conversation);
            const participant = conversation.other_user || conversation.participant || conversation.user || conversation;
            return <button key={userId || index} type="button" onClick={() => { setError(''); setSelectedUserId(userId); }} className={`flex w-full items-center gap-3 border-b border-[#f1edf7] px-4 py-3 text-left hover:bg-violet-50 ${selectedUserId === userId ? 'bg-violet-50' : ''}`}>
              <img src={personImage(participant) || `https://i.pravatar.cc/100?u=${encodeURIComponent(userId || name)}`} alt={name} className="h-10 w-10 shrink-0 rounded-full object-cover" />
              <span className="min-w-0"><span className="block truncate font-semibold text-[#24202e]">{name}</span>
              <span className="mt-1 block truncate text-xs text-[#706a80]">{conversation.last_message?.content || conversation.last_message || conversation.latest_message || ''}</span></span>
            </button>;
          })}
        </aside>

        <section className="flex min-h-[420px] flex-col">
          {selectedUserId ? <>
            <header className="border-b border-[#eeeaf5] p-4">
              <div className="flex items-center gap-3">
                <img src={partnerImage || 'https://i.pravatar.cc/100?img=1'} alt={partnerName} className="h-10 w-10 rounded-full object-cover" />
                <div><h2 className="font-bold">{partnerName}</h2><p className="text-xs text-[#706a80]">Chat participant</p></div>
              </div>
            </header>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {loadingMessages ? <p className="text-sm text-[#706a80]">Loading messages…</p> : messages.length === 0 ? <p className="text-sm text-[#706a80]">Start the conversation.</p> : messages.map((item, index) => {
                const senderId = String(item.sender_id || item.sender?.id || item.from_user_id || '');
                const mine = item.is_mine ?? item.is_sender ?? (senderId && currentUserId ? senderId === currentUserId : false);
                const senderName = mine ? currentUserName : item.sender?.name || item.sender_name || item.from_user?.name || partnerName;
                const senderImage = mine ? currentUserImage : personImage(item.sender) || item.sender_image || personImage(item.from_user) || partnerImage;
                return <div key={item.id || `${index}-${messageContent(item)}`} className={`flex max-w-[90%] items-end gap-2 ${mine ? 'ml-auto flex-row-reverse' : ''}`}>
                  <img src={senderImage || `https://i.pravatar.cc/100?u=${encodeURIComponent(senderId || selectedUserId)}`} alt={senderName} className="h-8 w-8 shrink-0 rounded-full object-cover" />
                  <div className={mine ? 'text-right' : ''}>
                    <p className="mb-1 px-1 text-[11px] text-[#706a80]">{senderName}</p>
                    <p className={`w-fit max-w-full rounded-xl px-4 py-2 text-left text-sm ${mine ? 'ml-auto bg-violet-600 text-white' : 'bg-violet-50 text-[#3d354c]'}`}>{messageContent(item)}</p>
                  </div>
                </div>;
              })}
            </div>
            <form onSubmit={submitMessage} className="flex gap-2 border-t border-[#eeeaf5] p-3">
              <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Type a message…" className="min-w-0 flex-1 rounded-lg bg-[#f8f6ff] px-3 py-2 text-sm outline-none ring-violet-300 focus:ring-2" />
              <button type="submit" disabled={sending || !draft.trim()} aria-label="Send message" className="rounded-lg bg-violet-600 p-2 text-white disabled:opacity-50"><Send className="h-4 w-4" /></button>
            </form>
          </> : <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-[#706a80]">Choose a conversation to start chatting.</div>}
        </section>
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>}
    </FeaturePage>
  );
}
