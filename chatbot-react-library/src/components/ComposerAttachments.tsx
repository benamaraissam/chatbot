import { FileText, X } from "lucide-react";
import type { PendingAttachment } from "../utils/attachments";
import { formatFileSize } from "../utils/messageParts";

interface ComposerAttachmentsProps {
  items: PendingAttachment[];
  onRemove: (id: string) => void;
}

export function ComposerAttachments({ items, onRemove }: ComposerAttachmentsProps) {
  if (items.length === 0) return null;

  return (
    <div className="cb-composer-attachments" role="list" aria-label="Attachments">
      {items.map((item) => {
        const isImage = item.previewUrl !== null;
        return (
          <div
            key={item.id}
            className={`cb-composer-attachment${isImage ? " cb-composer-attachment--image" : ""}`}
            role="listitem"
          >
            {isImage ? (
              <>
                <img
                  src={item.previewUrl!}
                  alt={item.file.name}
                  className="cb-composer-attachment-thumb"
                />
                <span className="cb-composer-attachment-meta cb-composer-attachment-meta--image">
                  <span className="cb-composer-attachment-name">{item.file.name}</span>
                </span>
              </>
            ) : (
              <span className="cb-composer-attachment-file" aria-hidden>
                <FileText size={16} />
              </span>
            )}
            {!isImage ? (
              <span className="cb-composer-attachment-meta">
                <span className="cb-composer-attachment-name">{item.file.name}</span>
                <span className="cb-composer-attachment-size">
                  {formatFileSize(item.file.size)}
                </span>
              </span>
            ) : null}
            <button
              type="button"
              className="cb-composer-attachment-remove"
              onClick={() => onRemove(item.id)}
              aria-label={`Remove ${item.file.name}`}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
