import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:omi/utils/analytics/mixpanel.dart';

class MeetingSummaryPage extends StatefulWidget {
  const MeetingSummaryPage({super.key});

  @override
  State<MeetingSummaryPage> createState() => _MeetingSummaryPageState();
}

class _MeetingSummaryPageState extends State<MeetingSummaryPage> {
  // Hardcoded demo data for meetings
  final List<Meeting> _meetings = [
    Meeting(
      id: '1',
      title: 'Product Strategy Review',
      date: DateTime.now().subtract(const Duration(days: 2)),
      duration: '45 min',
      participants: ['Sarah Johnson', 'Mike Chen', 'Alex Rodriguez'],
      summary: 'Discussed Q4 product roadmap priorities. Key decisions made on feature prioritization and resource allocation. Focus on user experience improvements and performance optimization.',
      actionItems: [
        ActionItem(
          id: '1',
          description: 'Prepare detailed feature specifications for mobile app redesign',
          assignee: 'Sarah Johnson',
          dueDate: DateTime.now().add(const Duration(days: 7)),
          priority: Priority.high,
        ),
        ActionItem(
          id: '2',
          description: 'Schedule user testing sessions for prototype validation',
          assignee: 'Mike Chen',
          dueDate: DateTime.now().add(const Duration(days: 5)),
          priority: Priority.medium,
        ),
        ActionItem(
          id: '3',
          description: 'Analyze competitor features and create comparison matrix',
          assignee: 'Alex Rodriguez',
          dueDate: DateTime.now().add(const Duration(days: 10)),
          priority: Priority.low,
        ),
      ],
    ),
    Meeting(
      id: '2',
      title: 'Weekly Team Standup',
      date: DateTime.now().subtract(const Duration(days: 1)),
      duration: '30 min',
      participants: ['John Smith', 'Emma Wilson', 'David Lee', 'Lisa Chang'],
      summary: 'Weekly progress updates and blockers discussion. Team velocity is improving. Identified need for additional resources on backend development.',
      actionItems: [
        ActionItem(
          id: '4',
          description: 'Update project timeline with current sprint velocity',
          assignee: 'John Smith',
          dueDate: DateTime.now().add(const Duration(days: 2)),
          priority: Priority.high,
        ),
        ActionItem(
          id: '5',
          description: 'Research and recommend backend optimization tools',
          assignee: 'David Lee',
          dueDate: DateTime.now().add(const Duration(days: 7)),
          priority: Priority.medium,
        ),
      ],
    ),
    Meeting(
      id: '3',
      title: 'Client Presentation Prep',
      date: DateTime.now().subtract(const Duration(hours: 3)),
      duration: '60 min',
      participants: ['Robert Brown', 'Jennifer Taylor', 'Mark Anderson'],
      summary: 'Finalized presentation materials for upcoming client demo. Rehearsed key talking points and identified potential client questions. Ready for tomorrow\'s presentation.',
      actionItems: [
        ActionItem(
          id: '6',
          description: 'Prepare backup demo environment in case of technical issues',
          assignee: 'Mark Anderson',
          dueDate: DateTime.now().add(const Duration(hours: 12)),
          priority: Priority.high,
        ),
        ActionItem(
          id: '7',
          description: 'Send follow-up materials to client after presentation',
          assignee: 'Jennifer Taylor',
          dueDate: DateTime.now().add(const Duration(days: 1)),
          priority: Priority.medium,
        ),
      ],
    ),
  ];

  @override
  void initState() {
    super.initState();
    // Track page view
    MixpanelManager().pageOpened('Meeting Summary');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              children: [
                const Icon(
                  FontAwesomeIcons.users,
                  size: 24,
                  color: Colors.white,
                ),
                const SizedBox(width: 12),
                const Text(
                  'Meeting Summary',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const Spacer(),
                Text(
                  '${_meetings.length} meetings',
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
          // Meeting List
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _meetings.length,
              itemBuilder: (context, index) {
                final meeting = _meetings[index];
                return _buildMeetingCard(meeting);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMeetingCard(Meeting meeting) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      color: Colors.grey[900],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Meeting header
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        meeting.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            FontAwesomeIcons.clock,
                            size: 12,
                            color: Colors.grey[400],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _formatDate(meeting.date),
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[400],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            FontAwesomeIcons.stopwatch,
                            size: 12,
                            color: Colors.grey[400],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            meeting.duration,
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[400],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            // Participants
            if (meeting.participants.isNotEmpty) ...[
              Row(
                children: [
                  Icon(
                    FontAwesomeIcons.users,
                    size: 14,
                    color: Colors.grey[400],
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      meeting.participants.join(', '),
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[300],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],

            // Summary
            Text(
              'Summary',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              meeting.summary,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[300],
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),

            // Action Items
            if (meeting.actionItems.isNotEmpty) ...[
              Text(
                'Action Items (${meeting.actionItems.length})',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 8),
              ...meeting.actionItems.map((actionItem) => _buildActionItem(actionItem)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionItem(ActionItem actionItem) {
    Color priorityColor;
    switch (actionItem.priority) {
      case Priority.high:
        priorityColor = Colors.red;
        break;
      case Priority.medium:
        priorityColor = Colors.orange;
        break;
      case Priority.low:
        priorityColor = Colors.green;
        break;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[800],
        borderRadius: BorderRadius.circular(8),
        border: Border(
          left: BorderSide(
            color: priorityColor,
            width: 4,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            actionItem.description,
            style: const TextStyle(
              fontSize: 14,
              color: Colors.white,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(
                FontAwesomeIcons.user,
                size: 12,
                color: Colors.grey[400],
              ),
              const SizedBox(width: 4),
              Text(
                actionItem.assignee,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[400],
                ),
              ),
              const SizedBox(width: 16),
              Icon(
                FontAwesomeIcons.calendar,
                size: 12,
                color: Colors.grey[400],
              ),
              const SizedBox(width: 4),
              Text(
                _formatDate(actionItem.dueDate),
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[400],
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: priorityColor.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  actionItem.priority.name.toUpperCase(),
                  style: TextStyle(
                    fontSize: 10,
                    color: priorityColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      if (difference.inHours == 0) {
        return '${difference.inMinutes}m ago';
      }
      return '${difference.inHours}h ago';
    } else if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else {
      final daysDiff = date.difference(now).inDays;
      if (daysDiff == 0) {
        return 'Today';
      } else if (daysDiff == 1) {
        return 'Tomorrow';
      } else {
        return 'In ${daysDiff}d';
      }
    }
  }
}

// Data models for demo purposes
class Meeting {
  final String id;
  final String title;
  final DateTime date;
  final String duration;
  final List<String> participants;
  final String summary;
  final List<ActionItem> actionItems;

  Meeting({
    required this.id,
    required this.title,
    required this.date,
    required this.duration,
    required this.participants,
    required this.summary,
    required this.actionItems,
  });
}

class ActionItem {
  final String id;
  final String description;
  final String assignee;
  final DateTime dueDate;
  final Priority priority;

  ActionItem({
    required this.id,
    required this.description,
    required this.assignee,
    required this.dueDate,
    required this.priority,
  });
}

enum Priority {
  high,
  medium,
  low,
}
