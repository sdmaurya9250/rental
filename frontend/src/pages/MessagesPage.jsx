import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
// import { 
//   Send, 
//   Search, 
//   SlidersHorizontal, 
//   Video, 
//   Phone, 
//   MoreVertical, 
//   Plus, 
//   Smile, 
//   Paperclip, 
//   Image as ImageIcon,
//   CheckCheck
// } from 'lucide-[#e7e1f2]'; // Adjust icon import path if needed
import { ArrowLeft, Send, Search, SlidersHorizontal, Video, Phone, MoreVertical, Plus, Smile, Paperclip, Image as ImageIcon, CheckCheck } from 'lucide-react';
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
  const [searchQuery, setSearchQuery] = useState('');
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
        setSelectedUserId((selected) => {
          if (selected || !items[0]) return selected;
          return window.matchMedia('(min-width: 768px)').matches ? conversationUserId(items[0]) : '';
        });
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

  const filteredConversations = useMemo(() => {
    return conversations.filter((item) =>
      conversationName(item).toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [conversations, searchQuery]);

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
        created_at: sent?.created_at || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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
    return (
      <FeaturePage title="Messages" subtitle="Finders and RentCoPartner can chat here.">
        <p className="text-sm text-amber-700">
          {error} <Link to="/?auth=login" className="font-semibold underline">Sign in</Link>
        </p>
      </FeaturePage>
    );
  }

  return (
    <FeaturePage title="Messages" subtitle="Finders and RentCoPartner can chat with each other here.">
      <div className="grid h-[min(76vh,750px)] min-h-[520px] max-w-6xl overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-lg shadow-violet-100/50 md:grid-cols-[minmax(250px,0.8fr)_minmax(0,1.5fr)]">
        
        {/* Left Sidebar */}
        <aside className={`${selectedUserId ? 'hidden' : 'flex'} min-h-0 flex-col border-b border-slate-100 md:flex md:border-b-0 md:border-r`}>
          {/* Search Header */}
          <div className="p-4">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-xl bg-slate-50 py-2.5 pl-10 pr-4 text-xs font-medium text-slate-700 placeholder-slate-400 outline-none transition focus:bg-slate-100"
                />
              </div>
              <button 
                type="button" 
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-500 hover:bg-slate-100"
              >
                <SlidersHorizontal className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            {loadingInbox ? (
              <p className="p-4 text-center text-xs text-slate-400">Loading conversations…</p>
            ) : filteredConversations.length === 0 ? (
              <p className="p-4 text-center text-xs text-slate-400">No conversations found.</p>
            ) : (
              filteredConversations.map((conversation, index) => {
                const userId = conversationUserId(conversation);
                const name = conversationName(conversation);
                const participant = conversation.other_user || conversation.participant || conversation.user || conversation;
                const isSelected = selectedUserId === userId;
                const unreadCount = conversation.unread_count || conversation.unread || 0;
                const time = conversation.time || conversation.last_message_time || '10:24 AM';

                return (
                  <button
                    key={userId || index}
                    type="button"
                    onClick={() => {
                      setError('');
                      setSelectedUserId(userId);
                    }}
                    className={`relative flex w-full items-center gap-3.5 px-4 py-3.5 text-left transition ${
                      isSelected ? 'bg-violet-50/60' : 'hover:bg-slate-50'
                    }`}
                  >
                    {/* Active Left Indicator Line */}
                    {isSelected && (
                      <span className="absolute left-0 top-0 bottom-0 w-1 rounded-r-full bg-violet-600" />
                    )}

                    {/* Avatar with Status Badge */}
                    <div className="relative shrink-0">
                      <img
                        src={personImage(participant) || `https://i.pravatar.cc/100?u=${encodeURIComponent(userId || name)}`}
                        alt={name}
                        width="44"
                        height="44"
                        loading="lazy"
                        className="h-11 w-11 rounded-full object-cover"
                      />
                      <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
                    </div>

                    {/* User Info & Message Preview */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="truncate text-sm font-semibold text-slate-800">{name}</h3>
                        <span className="text-[11px] font-medium text-slate-400">{time}</span>
                      </div>
                      <div className="mt-1 flex items-center justify-between gap-2">
                        <p className="truncate text-xs text-slate-500">
                          {conversation.last_message?.content || conversation.last_message || conversation.latest_message || 'Hey! Looking forward to it 😊'}
                        </p>
                        {unreadCount > 0 && (
                          <span className="flex h-4 min-w-[16px] shrink-0 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
                            {unreadCount}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </aside>

        {/* Right Section: Chat Panel */}
        <section className={`${selectedUserId ? 'flex' : 'hidden md:flex'} min-h-0 flex-col bg-slate-50/30`}>
          {selectedUserId ? (
            <>
              {/* Header */}
              <header className="flex items-center justify-between border-b border-slate-100 bg-white px-3 py-3 sm:px-6 sm:py-4">
                <div className="flex items-center gap-3">
                  <button type="button" onClick={() => setSelectedUserId('')} className="rounded-lg p-2 text-violet-700 hover:bg-violet-50 md:hidden" aria-label="Back to conversations"><ArrowLeft className="h-4 w-4" /></button>
                  <div className="relative">
                    <img
                      src={partnerImage || 'https://i.pravatar.cc/100?img=1'}
                      alt={partnerName}
                      width="40"
                      height="40"
                      loading="lazy"
                      className="h-10 w-10 rounded-full object-cover"
                    />
                    <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-800">{partnerName}</h2>
                    <p className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-600">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Online now
                    </p>
                  </div>
                </div>

                {/* Call & Action Controls */}
                {/* <div className="flex items-center gap-1 text-slate-400">
                  <button type="button" className="rounded-xl p-2.5 hover:bg-slate-100 hover:text-slate-600">
                    <Video className="h-4 w-4" />
                  </button>
                  <button type="button" className="rounded-xl p-2.5 hover:bg-slate-100 hover:text-slate-600">
                    <Phone className="h-4 w-4" />
                  </button>
                  <button type="button" className="rounded-xl p-2.5 hover:bg-slate-100 hover:text-slate-600">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div> */}
              </header>

              {/* Chat Thread */}
              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-3 sm:p-6">
                {/* Date Divider */}
                <div className="my-2 flex justify-center">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium text-slate-400">
                    Today
                  </span>
                </div>

                {loadingMessages ? (
                  <p className="text-center text-xs text-slate-400">Loading messages…</p>
                ) : messages.length === 0 ? (
                  <p className="text-center text-xs text-slate-400">Start the conversation.</p>
                ) : (
                  messages.map((item, index) => {
                    const senderId = String(item.sender_id || item.sender?.id || item.from_user_id || '');
                    const mine = item.is_mine ?? item.is_sender ?? (senderId && currentUserId ? senderId === currentUserId : false);
                    const senderName = mine ? currentUserName : item.sender?.name || item.sender_name || partnerName;
                    const senderImage = mine ? currentUserImage : personImage(item.sender) || partnerImage;
                    const time = item.created_at || '10:20 AM';

                    return (
                      <div
                        key={item.id || `${index}-${messageContent(item)}`}
                        className={`flex items-end gap-2.5 ${mine ? 'justify-end' : 'justify-start'}`}
                      >
                        {/* Avatar for Incoming Messages */}
                        {!mine && (
                          <img
                            src={senderImage || `https://i.pravatar.cc/100?u=${encodeURIComponent(senderId || selectedUserId)}`}
                            alt={senderName}
                            width="28"
                            height="28"
                            loading="lazy"
                            className="h-7 w-7 rounded-full object-cover"
                          />
                        )}

                        {/* Message Bubble Container */}
                        <div className={`flex items-end gap-2 max-w-[70%] ${mine ? 'flex-row-reverse' : 'flex-row'}`}>
                          <div
                            className={`rounded-2xl px-4 py-2.5 text-xs font-normal leading-relaxed ${
                              mine
                                ? 'bg-violet-600 text-white rounded-br-none shadow-md shadow-violet-200'
                                : 'bg-slate-100 text-slate-700 rounded-bl-none'
                            }`}
                          >
                            {messageContent(item)}
                          </div>

                          {/* Time & Read Status */}
                          <div className="flex items-center gap-1 shrink-0 pb-1 text-[10px] text-slate-400">
                            <span>{time}</span>
                            {mine && <CheckCheck className="h-3 w-3 text-violet-400" />}
                          </div>
                        </div>

                        {/* Avatar for Outgoing Messages */}
                        {mine && (
                          <img
                            src={senderImage || `https://i.pravatar.cc/100?u=${encodeURIComponent(currentUserId)}`}
                            alt={senderName}
                            width="28"
                            height="28"
                            loading="lazy"
                            className="h-7 w-7 rounded-full object-cover"
                          />
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              {/* Message Input Box */}
              <div className="p-4 bg-white border-t border-slate-100">
                <form onSubmit={submitMessage} className="flex items-center gap-2">
                  <button
                    type="button"
                    className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 transition"
                  >
                    <Plus className="h-4 w-4" />
                  </button>

                  <div className="relative flex flex-1 items-center">
                    <input
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      placeholder="Type a message..."
                      className="w-full rounded-2xl bg-slate-50 py-2.5 pl-4 pr-24 text-xs text-slate-700 placeholder-slate-400 outline-none transition focus:bg-slate-100"
                    />

                    {/* Action icons in input */}
                    <div className="absolute right-3 flex items-center gap-2 text-slate-400">
                      <button type="button" className="hover:text-slate-600">
                        <Smile className="h-4 w-4" />
                      </button>
                      <button type="button" className="hover:text-slate-600">
                        <Paperclip className="h-4 w-4" />
                      </button>
                      <button type="button" className="hover:text-slate-600">
                        <ImageIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={sending || !draft.trim()}
                    className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600 text-white shadow-md shadow-violet-200 transition hover:bg-violet-700 disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center p-6 text-center text-xs text-slate-400">
              Select a conversation to start chatting.
            </div>
          )}
        </section>
      </div>

      {error && <p role="alert" className="mt-3 text-center text-xs font-medium text-rose-500">{error}</p>}
    </FeaturePage>
  );
}
