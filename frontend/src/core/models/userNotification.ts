export interface UserNotification {
  status: "success" | "info" | "warning" | "error";
  message: string;
}
