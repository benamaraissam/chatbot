import { ArrowUp, Paperclip, Square } from "lucide-react";
import {
  type ChangeEvent,
  type FormEvent,
  type KeyboardEvent,
  useRef,
  useState,
} from "react";
import { useChatbot, useChatbotActions, useStreamingChat } from "../hooks";
import { useChatbotContext } from "../core/context";
import { registerDisplayUrl } from "../utils/attachmentDisplay";
import {
  DEFAULT_ATTACHMENT_ACCEPT,
  detachPendingAttachments,
  filesToAttachmentParts,
  pendingAttachmentsToParts,
  validateAttachmentBatch,
} from "../utils/attachments";
import { createId } from "../utils/id";
import { ComposerAttachments } from "./ComposerAttachments";

export function ChatInput() {
  const { sendMessage, stopStreaming } = useChatbotActions();
  const { isStreaming } = useStreamingChat();
  const { config, store } = useChatbotContext();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [input, setInput] = useState("");
  const [attachError, setAttachError] = useState<string | null>(null);
  const [isReadingFiles, setIsReadingFiles] = useState(false);
  const attachments = useChatbot((s) => s.composerAttachments);
  const addComposerAttachments = useChatbot((s) => s.addComposerAttachments);
  const removeComposerAttachment = useChatbot((s) => s.removeComposerAttachment);
  const clearComposerAttachments = useChatbot((s) => s.clearComposerAttachments);

  const placeholder = config.placeholder ?? "Message…";
  const attachmentsEnabled = config.attachments?.enabled !== false;
  const accept = config.attachments?.accept ?? DEFAULT_ATTACHMENT_ACCEPT;
  const limits = {
    maxCount: config.attachments?.maxCount,
    maxSizeBytes: config.attachments?.maxSizeBytes,
  };
  const canSend =
    (input.trim().length > 0 || attachments.length > 0) && !isStreaming;

  const openFilePicker = () => {
    if (!attachmentsEnabled || isStreaming || isReadingFiles) return;
    fileInputRef.current?.click();
  };

  const onFilesSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    const list = e.target.files;
    if (!list?.length) return;

    setAttachError(null);
    setIsReadingFiles(true);
    const files = Array.from(list);

    const err = validateAttachmentBatch(
      files,
      store.getState().composerAttachments.length,
      limits,
    );
    if (err) {
      setAttachError(err);
      setIsReadingFiles(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    try {
      const next = await filesToAttachmentParts(files, () => createId("att"));
      addComposerAttachments(next);
    } catch {
      setAttachError("Could not read one or more files.");
    } finally {
      setIsReadingFiles(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const submit = async () => {
    const text = input.trim();
    const pending = store.getState().composerAttachments;
    if ((!text && pending.length === 0) || isStreaming) return;

    const attachmentParts = pendingAttachmentsToParts(pending);
    for (const part of attachmentParts) {
      if (part.type === "image" && part.displayUrl) {
        registerDisplayUrl(part.displayUrl);
      }
    }
    detachPendingAttachments(pending);
    clearComposerAttachments({ revoke: false });
    setInput("");
    setAttachError(null);
    await sendMessage(text, { attachmentParts });
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submit();
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  return (
    <div className="cb-shrink-0 cb-border-t cb-border-cb-border cb-bg-cb-surface cb-p-3">
      <ComposerAttachments items={attachments} onRemove={removeComposerAttachment} />
      {isReadingFiles ? (
        <p className="cb-composer-attach-status" aria-live="polite">
          Reading file…
        </p>
      ) : null}
      {attachError ? (
        <p className="cb-composer-attach-error" role="alert">
          {attachError}
        </p>
      ) : null}
      <form
        onSubmit={onSubmit}
        className="cb-composer-shell cb-relative cb-flex cb-flex-col cb-gap-2 cb-p-2"
      >
        {attachmentsEnabled ? (
          <input
            ref={fileInputRef}
            type="file"
            className="cb-file-input-hidden"
            accept={accept}
            multiple
            tabIndex={-1}
            aria-hidden
            onChange={(e) => void onFilesSelected(e)}
          />
        ) : null}
        <div className="cb-flex cb-items-end cb-gap-1">
          {attachmentsEnabled ? (
            <button
              type="button"
              onClick={openFilePicker}
              disabled={isStreaming || isReadingFiles}
              className="cb-composer-attach"
              aria-label="Attach files or images"
            >
              <Paperclip size={18} />
            </button>
          ) : null}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={isStreaming}
            className="cb-composer-textarea cb-max-h-[120px] cb-min-h-[36px] cb-flex-1 cb-resize-none cb-border-0 cb-bg-transparent cb-py-2 cb-pl-1 cb-pr-1 cb-text-[13px] cb-leading-[1.45] cb-text-cb-text cb-outline-none placeholder:cb-text-cb-muted disabled:cb-opacity-50"
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={stopStreaming}
              className="cb-composer-action cb-composer-action--stop"
              aria-label="Stop generating"
            >
              <Square size={14} fill="currentColor" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              className="cb-composer-action cb-composer-action--send"
              aria-label="Send message"
            >
              <ArrowUp size={16} strokeWidth={2.5} />
            </button>
          )}
        </div>
      </form>
      <p className="cb-mt-2 cb-text-center cb-text-[10px] cb-text-cb-muted">
        Enter to send · Shift+Enter for new line
        {attachmentsEnabled ? " · Attach images or files" : ""}
      </p>
    </div>
  );
}