
import ipaddress
import json
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain.tools import tool


def _validate_public_url(url: str) -> str:
    """Allow HTTPS URLs pointing to publicly routable hosts only."""
    parsed = urlparse(url.strip())

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Please provide a valid HTTPS event URL.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed.")

    host = parsed.hostname.lower()

    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Local network URLs are not allowed.")

    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        except socket.gaierror as exc:
            raise ValueError("The event website could not be resolved.") from exc

    if not addresses or any(
        not address.is_global for address in addresses
    ):
        raise ValueError("Private or non-public network addresses are not allowed.")

    return url.strip()


@tool
def inspect_event_link(url: str) -> str:
    """Inspect a public event webpage for its title, date, time, location,
    organizer, description, and registration or joining links.

    Args:
        url: HTTPS URL copied from WhatsApp or another source.
    """
    try:
        current_url = _validate_public_url(url)

        # Handle redirects manually so each destination is validated.
        with requests.Session() as session:
            session.headers.update({
                "User-Agent": "ProductivityMeetingAgent/1.0"
            })

            response = None

            for _ in range(4):
                response = session.get(
                    current_url,
                    timeout=(10, 45),
                    allow_redirects=False,
                    stream=True,
                )

                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("Location")
                    response.close()

                    if not location:
                        return "The event website returned an invalid redirect."

                    from urllib.parse import urljoin
                    current_url = _validate_public_url(
                        urljoin(current_url, location)
                    )
                    continue

                break
            else:
                return "The event page redirected too many times."

            if response is None:
                return "The event page could not be retrieved."

            with response:
                if response.status_code >= 400:
                    return (
                        f"The event website returned HTTP "
                        f"{response.status_code}. The page may require login "
                        "or may block automated access."
                    )

                content_type = response.headers.get("Content-Type", "")
                if "html" not in content_type.lower():
                    return "The URL did not return an HTML webpage."

                # Limit how much HTML is read.
                chunks = []
                total = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    remaining = 1_000_000 - total
                    if remaining <= 0:
                        break
                    chunk = chunk[:remaining]
                    chunks.append(chunk)
                    total += len(chunk)
                    if total >= 1_000_000:
                        break

                html = b"".join(chunks).decode(
                    response.encoding or "utf-8",
                    errors="replace",
                )

        soup = BeautifulSoup(html, "html.parser")

        def meta_content(*names):
            for name in names:
                tag = soup.find("meta", attrs={"property": name})
                if not tag:
                    tag = soup.find("meta", attrs={"name": name})
                if tag and tag.get("content"):
                    return tag["content"].strip()
            return ""

        result = {
            "source_url": current_url,
            "page_title": soup.title.get_text(" ", strip=True) if soup.title else "",
            "description": meta_content(
                "og:description", "description", "twitter:description"
            ),
            "event_metadata": [],
            "visible_text_excerpt": soup.get_text(" ", strip=True)[:5000],
        }

        # Extract structured event metadata where the site provides it.
        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue

            objects = data if isinstance(data, list) else [data]

            for item in objects:
                if not isinstance(item, dict):
                    continue

                graph = item.get("@graph", [])
                candidates = [item]
                if isinstance(graph, list):
                    candidates.extend(
                        node for node in graph if isinstance(node, dict)
                    )

                for candidate in candidates:
                    kind = candidate.get("@type", "")
                    kinds = kind if isinstance(kind, list) else [kind]

                    if any("Event" in str(value) for value in kinds):
                        result["event_metadata"].append({
                            "name": candidate.get("name"),
                            "startDate": candidate.get("startDate"),
                            "endDate": candidate.get("endDate"),
                            "eventStatus": candidate.get("eventStatus"),
                            "eventAttendanceMode": candidate.get(
                                "eventAttendanceMode"
                            ),
                            "description": candidate.get("description"),
                            "location": candidate.get("location"),
                            "organizer": candidate.get("organizer"),
                            "offers": candidate.get("offers"),
                            "url": candidate.get("url"),
                        })

        return json.dumps(result, indent=2, ensure_ascii=False)

    except requests.RequestException as exc:
        return f"Could not retrieve the event page: {type(exc).__name__}."
    except ValueError as exc:
        return f"Could not inspect that URL: {exc}"
