import { ChatWindow } from "./ChatWindow";
import { FloatingButton } from "./FloatingButton";

/** All-in-one floating chat UI (button + window). */
export function FloatingChatbot() {
  return (
    <>
      <FloatingButton />
      <ChatWindow />
    </>
  );
}
