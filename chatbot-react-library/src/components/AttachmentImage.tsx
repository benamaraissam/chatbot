import { useEffect, useState } from "react";
import type { ImagePart } from "../types";
import { createBlobUrlFromBase64, revokeDisplayUrl } from "../utils/attachmentDisplay";

interface AttachmentImageProps {
  part: ImagePart;
  className?: string;
}

export function AttachmentImage({ part, className }: AttachmentImageProps) {
  const label = part.name ?? "Image";
  const [src, setSrc] = useState<string | null>(part.displayUrl ?? null);

  useEffect(() => {
    if (part.displayUrl) {
      setSrc(part.displayUrl);
      return;
    }
    if (!part.data?.trim()) {
      setSrc(null);
      return;
    }
    const url = createBlobUrlFromBase64(part.mimeType, part.data);
    setSrc(url);
    return () => revokeDisplayUrl(url ?? undefined);
  }, [part.displayUrl, part.mimeType, part.data]);

  if (!src) {
    return (
      <div className="cb-attachment-image-missing" role="status">
        Image unavailable
      </div>
    );
  }

  return <img src={src} alt={label} className={className} loading="lazy" />;
}
