/*
 * Public API Surface of chatbot-angular
 */

export * from './lib/types';
export * from './lib/transport/sse-client';
export * from './lib/tokens/chatbot-config.token';
export * from './lib/services/chatbot.service';

// Utils (commonly needed by consumers)
export type { PendingAttachment } from './lib/utils/attachments';
export { DEFAULT_ATTACHMENT_ACCEPT, validateAttachmentBatch, filesToAttachmentParts, pendingAttachmentsToParts, detachPendingAttachments, withImageDefaultText } from './lib/utils/attachments';
export { registerDisplayUrl } from './lib/utils/attachment-display';
export { createId } from './lib/utils/id';
export { formatFileSize, getMessageText, isFilePart, isImageLikePart } from './lib/utils/message-parts';
export { getToolsForMessage, formatToolName, getToolInputSummary, formatToolInput } from './lib/utils/thread';
export type { ThemeMode, ResolvedTheme } from './lib/utils/theme';
export { resolveTheme } from './lib/utils/theme';
export { buildPrimaryColorStyle, parseColor } from './lib/utils/primaryColor';

// Components
export { ComposerAttachmentsComponent } from './lib/components/composer-attachments/composer-attachments.component';
export { ChatInputComponent } from './lib/components/chat-input/chat-input.component';
export { ChatHeaderComponent } from './lib/components/chat-header/chat-header.component';
export { MessageListComponent } from './lib/components/message-list/message-list.component';
export { ChatWindowComponent } from './lib/components/chat-window/chat-window.component';
export { FloatingChatbotComponent } from './lib/components/floating-chatbot/floating-chatbot.component';
export { FloatingButtonComponent } from './lib/components/floating-button/floating-button.component';
export { MessageBubbleComponent } from './lib/components/message-bubble/message-bubble.component';
export { AssistantTurnComponent } from './lib/components/assistant-turn/assistant-turn.component';
export { ToolCallCardComponent } from './lib/components/tool-call-card/tool-call-card.component';
export { MarkdownMessageComponent } from './lib/components/markdown-message/markdown-message.component';
export { BotAvatarComponent } from './lib/components/bot-avatar/bot-avatar.component';
export { StreamingCursorComponent } from './lib/components/streaming-cursor/streaming-cursor.component';
export { CopyButtonComponent } from './lib/components/copy-button/copy-button.component';
export { ThinkingIndicatorComponent } from './lib/components/thinking-indicator/thinking-indicator.component';
export { StreamingAnswerIndicatorComponent } from './lib/components/streaming-answer-indicator/streaming-answer-indicator.component';
export { MessageAttachmentsComponent } from './lib/components/message-attachments/message-attachments.component';
export { PendingAssistantTurnComponent } from './lib/components/pending-assistant-turn/pending-assistant-turn.component';
