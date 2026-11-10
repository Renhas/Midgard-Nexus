export function readCookie(cookieString, name) {
  const value = `; ${cookieString || ""}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}
