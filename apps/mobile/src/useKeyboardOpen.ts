import { useEffect, useState } from "react";
import { Keyboard } from "react-native";

export function useKeyboardOpen(): boolean {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const shown = Keyboard.addListener("keyboardDidShow", () => setOpen(true));
    const hidden = Keyboard.addListener("keyboardDidHide", () => setOpen(false));
    return () => {
      shown.remove();
      hidden.remove();
    };
  }, []);

  return open;
}
