"""Mock Wazuh SIEM client generating realistic synthetic SOC alerts and agent telemetry."""
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from app.wazuh.client import WazuhClient


class MockWazuhClient(WazuhClient):
    """Deterministic synthetic data generator simulating a real Wazuh SIEM instance."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._agents = self._init_agents()
        self._alerts = self._init_alerts()
        self._alerts_by_id = {a["id"]: a for a in self._alerts}

    def _init_agents(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": "000",
                "name": "wazuh-manager-master",
                "ip": "127.0.0.1",
                "status": "active",
                "os": {"name": "Ubuntu", "platform": "ubuntu", "version": "22.04.4 LTS", "arch": "x86_64"},
                "version": "Wazuh v4.8.0",
                "last_keepalive": now.isoformat(),
            },
            {
                "id": "001",
                "name": "linux-srv-prod01",
                "ip": "192.168.1.10",
                "status": "active",
                "os": {"name": "Ubuntu", "platform": "ubuntu", "version": "22.04.4 LTS", "arch": "x86_64"},
                "version": "Wazuh v4.8.0",
                "last_keepalive": (now - timedelta(seconds=12)).isoformat(),
            },
            {
                "id": "002",
                "name": "win-desktop-fin01",
                "ip": "192.168.1.25",
                "status": "active",
                "os": {"name": "Windows", "platform": "windows", "version": "11 Enterprise", "arch": "x86_64"},
                "version": "Wazuh v4.8.0",
                "last_keepalive": (now - timedelta(seconds=28)).isoformat(),
            },
            {
                "id": "003",
                "name": "pfsense-firewall",
                "ip": "192.168.1.1",
                "status": "active",
                "os": {"name": "FreeBSD", "platform": "bsd", "version": "14.0-RELEASE", "arch": "x86_64"},
                "version": "Wazuh v4.8.0 (syslog)",
                "last_keepalive": (now - timedelta(seconds=5)).isoformat(),
            },
            {
                "id": "004",
                "name": "dev-linux-node02",
                "ip": "192.168.1.55",
                "status": "disconnected",
                "os": {"name": "Debian", "platform": "debian", "version": "12.5 (bookworm)", "arch": "x86_64"},
                "version": "Wazuh v4.8.0",
                "last_keepalive": (now - timedelta(hours=6, minutes=42)).isoformat(),
            },
        ]

    def _init_alerts(self) -> list[dict[str, Any]]:
        rng = random.Random(self.seed)
        now = datetime.now(timezone.utc)
        alerts: list[dict[str, Any]] = []

        # Templates for 3 MVP telemetry classes
        templates = [
            # 1. Linux host (auth, ssh, auditd, sudo)
            {
                "agent_id": "001",
                "agent_name": "linux-srv-prod01",
                "agent_ip": "192.168.1.10",
                "location": "/var/log/auth.log",
                "rule_id": "5710",
                "rule_desc": "sshd: Attempt to login using a non-existent user",
                "level": 5,
                "mitre": {"id": ["T1110.001"], "tactic": ["Credential Access"]},
                "log_tmpl": "sshd[{pid}]: Invalid user admin from {src_ip} port {src_port}",
                "data_tmpl": {"srcip": "{src_ip}", "dstuser": "admin"},
            },
            {
                "agent_id": "001",
                "agent_name": "linux-srv-prod01",
                "agent_ip": "192.168.1.10",
                "location": "/var/log/auth.log",
                "rule_id": "5712",
                "rule_desc": "sshd: SSH brute force attack detected (multiple authentication failures)",
                "level": 10,
                "mitre": {"id": ["T1110"], "tactic": ["Credential Access"]},
                "log_tmpl": "sshd[{pid}]: PAM 5 more authentication failures; logname= uid=0 euid=0 tty=ssh ruser= rhost={src_ip} user=root",
                "data_tmpl": {"srcip": "{src_ip}", "dstuser": "root"},
            },
            {
                "agent_id": "001",
                "agent_name": "linux-srv-prod01",
                "agent_ip": "192.168.1.10",
                "location": "/var/log/secure",
                "rule_id": "5402",
                "rule_desc": "sudo: Successful sudo execution by unauthorized user",
                "level": 8,
                "mitre": {"id": ["T1078", "T1548.003"], "tactic": ["Privilege Escalation", "Defense Evasion"]},
                "log_tmpl": "sudo: fayssal : TTY=pts/1 ; PWD=/home/fayssal ; USER=root ; COMMAND=/bin/bash",
                "data_tmpl": {"srcuser": "fayssal", "dstuser": "root", "command": "/bin/bash"},
            },
            {
                "agent_id": "001",
                "agent_name": "linux-srv-prod01",
                "agent_ip": "192.168.1.10",
                "location": "audit",
                "rule_id": "80700",
                "rule_desc": "auditd: /etc/shadow modified or read attempt",
                "level": 12,
                "mitre": {"id": ["T1003.008"], "tactic": ["Credential Access"]},
                "log_tmpl": "type=SYSCALL msg=audit({epoch}): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=7ffd3a a2=0 a3=0 items=1 ppid=1204 pid=1892 auid=1001 uid=0 gid=0 euid=0 tty=pts1 ses=4 comm=\"cat\" exe=\"/bin/cat\" key=\"shadow-watch\"",
                "data_tmpl": {"audit": {"type": "SYSCALL", "key": "shadow-watch", "command": "/bin/cat", "target": "/etc/shadow"}},
            },
            # 2. Windows host (Sysmon: process creation, powershell, registry)
            {
                "agent_id": "002",
                "agent_name": "win-desktop-fin01",
                "agent_ip": "192.168.1.25",
                "location": "EventChannel: Microsoft-Windows-Sysmon/Operational",
                "rule_id": "60100",
                "rule_desc": "Sysmon - Event 1: Suspicious PowerShell encoded command execution",
                "level": 12,
                "mitre": {"id": ["T1059.001", "T1027"], "tactic": ["Execution", "Defense Evasion"]},
                "log_tmpl": "Event 1, Process Create: Image: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe CommandLine: powershell.exe -nop -w hidden -enc JABjAGwAaQBlAG4AdAAg... ParentImage: C:\\Windows\\explorer.exe User: FIN-CORP\\alice",
                "data_tmpl": {"win": {"eventdata": {"image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "user": "FIN-CORP\\alice", "parentImage": "C:\\Windows\\explorer.exe"}}},
            },
            {
                "agent_id": "002",
                "agent_name": "win-desktop-fin01",
                "agent_ip": "192.168.1.25",
                "location": "EventChannel: Microsoft-Windows-Sysmon/Operational",
                "rule_id": "60115",
                "rule_desc": "Sysmon - Event 3: Suspicious network connection to public IP on non-standard port",
                "level": 7,
                "mitre": {"id": ["T1071.001"], "tactic": ["Command and Control"]},
                "log_tmpl": "Event 3, Network Connect: Image: C:\\Users\\alice\\AppData\\Local\\Temp\\update.exe SourceIp: 192.168.1.25 DestinationIp: 185.220.101.5 DestinationPort: 4444 Protocol: tcp",
                "data_tmpl": {"win": {"eventdata": {"destinationIp": "185.220.101.5", "destinationPort": "4444", "protocol": "tcp"}}},
            },
            {
                "agent_id": "002",
                "agent_name": "win-desktop-fin01",
                "agent_ip": "192.168.1.25",
                "location": "EventChannel: Microsoft-Windows-Sysmon/Operational",
                "rule_id": "60150",
                "rule_desc": "Sysmon - Event 13: Registry value modified for persistence (Run key)",
                "level": 11,
                "mitre": {"id": ["T1547.001"], "tactic": ["Persistence", "Privilege Escalation"]},
                "log_tmpl": "Event 13, RegistryEvent: TargetObject: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WinSecurityDetails Details: C:\\Users\\Public\\updater.exe",
                "data_tmpl": {"win": {"eventdata": {"targetObject": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WinSecurityDetails"}}},
            },
            {
                "agent_id": "002",
                "agent_name": "win-desktop-fin01",
                "agent_ip": "192.168.1.25",
                "location": "EventChannel: Microsoft-Windows-Security-Auditing",
                "rule_id": "60010",
                "rule_desc": "Windows logon failure - Bad password",
                "level": 5,
                "mitre": {"id": ["T1078.002"], "tactic": ["Defense Evasion", "Persistence"]},
                "log_tmpl": "Event 4625: An account failed to log on. Subject User Name: - Target User Name: bob Status: 0xc000006d Sub Status: 0xc000006a",
                "data_tmpl": {"win": {"system": {"eventID": "4625"}, "eventdata": {"targetUserName": "bob"}}},
            },
            # 3. Network perimeter / Firewall (pfSense syslog)
            {
                "agent_id": "003",
                "agent_name": "pfsense-firewall",
                "agent_ip": "192.168.1.1",
                "location": "/var/log/filter.log",
                "rule_id": "87100",
                "rule_desc": "pfSense: Firewall blocked inbound connection on WAN (Port Scan)",
                "level": 6,
                "mitre": {"id": ["T1046"], "tactic": ["Discovery"]},
                "log_tmpl": "filterlog[120]: 4,,,1000000103,igb0,match,block,in,4,0x0,,64,0,0,DF,6,tcp,60,{src_ip},203.0.113.45,{src_port},445,0,S,1234567890,,1024,,",
                "data_tmpl": {"srcip": "{src_ip}", "dstip": "203.0.113.45", "dstport": "445", "action": "block"},
            },
            {
                "agent_id": "003",
                "agent_name": "pfsense-firewall",
                "agent_ip": "192.168.1.1",
                "location": "/var/log/filter.log",
                "rule_id": "87105",
                "rule_desc": "pfSense: Outbound traffic blocked by Snort/Suricata signature (Known C2 server)",
                "level": 14,
                "mitre": {"id": ["T1071"], "tactic": ["Command and Control"]},
                "log_tmpl": "snort[4301]: [1:2018959:4] ET CURRENT_EVENTS Suspicious Inbound Cobalt Strike Beaconing detected [Classification: A Network Trojan was detected] [Priority: 1] {TCP} 192.168.1.25:49821 -> 185.220.101.5:4444",
                "data_tmpl": {"srcip": "192.168.1.25", "dstip": "185.220.101.5", "dstport": "4444", "alert": "Cobalt Strike Beaconing"},
            },
            {
                "agent_id": "003",
                "agent_name": "pfsense-firewall",
                "agent_ip": "192.168.1.1",
                "location": "/var/log/filter.log",
                "rule_id": "87110",
                "rule_desc": "pfSense: Multiple dropped UDP packets from external subnet",
                "level": 4,
                "mitre": {"id": ["T1046"], "tactic": ["Discovery"]},
                "log_tmpl": "filterlog[120]: 5,,,1000000103,igb0,match,block,in,4,0x0,,64,0,0,DF,17,udp,48,{src_ip},203.0.113.45,{src_port},53,28",
                "data_tmpl": {"srcip": "{src_ip}", "dstip": "203.0.113.45", "dstport": "53", "action": "block"},
            },
        ]

        external_ips = ["45.33.32.156", "198.51.100.23", "185.220.101.5", "103.21.244.0", "91.240.118.172", "194.26.29.112"]

        # Generate 160 alerts spread over past 48 hours
        total_alerts = 160
        # Time distribution: more recent alerts, fewer older alerts
        time_offsets_minutes = sorted(
            [int(rng.expovariate(1 / 700)) for _ in range(total_alerts)],
            reverse=True,
        )

        for i, offset_min in enumerate(time_offsets_minutes):
            offset_min = min(offset_min, 48 * 60)  # cap at 48 hours
            ts = now - timedelta(minutes=offset_min, seconds=rng.randint(0, 59))
            tmpl = templates[i % len(templates)]

            alert_id = f"wazuh-alert-{i + 1:04d}-{ts.strftime('%Y%m%d%H%M')}"
            src_ip = rng.choice(external_ips)
            src_port = str(rng.randint(1024, 65535))
            pid = str(rng.randint(1000, 9999))
            epoch = str(int(ts.timestamp()))

            full_log = (
                tmpl["log_tmpl"]
                .replace("{src_ip}", src_ip)
                .replace("{src_port}", src_port)
                .replace("{pid}", pid)
                .replace("{epoch}", epoch)
            )

            data_rendered: dict[str, Any] = {}
            for k, v in tmpl["data_tmpl"].items():
                if isinstance(v, str):
                    data_rendered[k] = v.replace("{src_ip}", src_ip).replace("{src_port}", src_port)
                else:
                    data_rendered[k] = v

            alert = {
                "id": alert_id,
                "timestamp": ts.isoformat(),
                "rule": {
                    "id": tmpl["rule_id"],
                    "description": tmpl["rule_desc"],
                    "level": tmpl["level"],
                    "mitre": tmpl["mitre"],
                },
                "agent": {
                    "id": tmpl["agent_id"],
                    "name": tmpl["agent_name"],
                    "ip": tmpl["agent_ip"],
                },
                "location": tmpl["location"],
                "full_log": full_log,
                "data": data_rendered,
            }
            alerts.append(alert)

        # Sort newest first
        alerts.sort(key=lambda a: a["timestamp"], reverse=True)
        return alerts

    async def get_alerts(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        severity_min: int | None = None,
        status: str | None = None,
        agent_id: str | None = None,
        rule_id: str | None = None,
        since: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        filtered = self._alerts

        if severity_min is not None:
            filtered = [a for a in filtered if a["rule"]["level"] >= severity_min]

        if agent_id is not None:
            filtered = [a for a in filtered if a["agent"]["id"] == agent_id]

        if rule_id is not None:
            filtered = [a for a in filtered if a["rule"]["id"] == rule_id]

        if since is not None:
            since_iso = since.isoformat()
            filtered = [a for a in filtered if a["timestamp"] >= since_iso]

        total_count = len(filtered)
        paginated = filtered[offset : offset + limit]
        return paginated, total_count

    async def get_alert(self, wazuh_alert_id: str) -> dict[str, Any] | None:
        return self._alerts_by_id.get(wazuh_alert_id)

    async def get_agents(self) -> list[dict[str, Any]]:
        return self._agents

    async def get_stats_overview(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        cutoff_24h = (now - timedelta(hours=24)).isoformat()
        alerts_24h = [a for a in self._alerts if a["timestamp"] >= cutoff_24h]

        # Severity breakdown
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for a in alerts_24h:
            lvl = a["rule"]["level"]
            if lvl <= 4:
                severity_counts["low"] += 1
            elif lvl <= 7:
                severity_counts["medium"] += 1
            elif lvl <= 11:
                severity_counts["high"] += 1
            else:
                severity_counts["critical"] += 1

        # Top rules
        rule_counter = Counter(a["rule"]["id"] for a in alerts_24h)
        top_rules = []
        for r_id, count in rule_counter.most_common(5):
            sample = next(a for a in alerts_24h if a["rule"]["id"] == r_id)
            top_rules.append({
                "rule_id": r_id,
                "description": sample["rule"]["description"],
                "level": sample["rule"]["level"],
                "count": count,
            })

        # Top agents
        agent_counter = Counter(a["agent"]["name"] for a in alerts_24h)
        top_agents = [
            {"agent_name": name, "count": count}
            for name, count in agent_counter.most_common(5)
        ]

        return {
            "alerts_last_24h": len(alerts_24h),
            "severity_breakdown": severity_counts,
            "top_rules": top_rules,
            "top_agents": top_agents,
        }
