import { motion } from "framer-motion";
import { MessageCircle } from "lucide-react";
import { useChatbot, useChatbotActions } from "../hooks";

export function FloatingButton() {
  const isOpen = useChatbot((s) => s.isOpen);
  const { toggleOpen } = useChatbotActions();

  if (isOpen) return null;

  return (
    <motion.button
      type="button"
      onClick={toggleOpen}
      aria-label="Open chat"
      className="cb-fab"
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 26 }}
    >
      <MessageCircle size={24} strokeWidth={2} />
    </motion.button>
  );
}
