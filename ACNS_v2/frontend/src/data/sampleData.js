const sampleIssues = [
  {
    id: '1',
    category: 'Electrical',
    description: 'Broken street light near main entrance',
    status: 'Open',
    location: { lat: 17.3850, lng: 78.4867, text: 'Main Building Entrance' },
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    category: 'Plumbing',
    description: 'Water leak in restroom',
    status: 'In Progress',
    location: { lat: 17.3860, lng: 78.4870, text: 'Science Block Restroom' },
    createdAt: '2024-01-14T09:00:00Z',
    updatedAt: '2024-01-15T14:00:00Z'
  },
  {
    id: '3',
    category: 'Maintenance',
    description: 'Broken bench in park area',
    status: 'Resolved',
    location: { lat: 17.3855, lng: 78.4850, text: 'Central Park' },
    createdAt: '2024-01-10T11:00:00Z',
    updatedAt: '2024-01-12T16:00:00Z'
  },
  {
    id: '4',
    category: 'Electrical',
    description: 'Flickering lights in classroom 201',
    status: 'Closed',
    location: { lat: 17.3870, lng: 78.4880, text: 'Engineering Building Room 201' },
    createdAt: '2024-01-05T08:00:00Z',
    updatedAt: '2024-01-06T12:00:00Z'
  },
  {
    id: '5',
    category: 'Sanitation',
    description: 'Overflowing trash bins',
    status: 'Open',
    location: { lat: 17.3840, lng: 78.4860, text: 'Cafeteria Area' },
    createdAt: '2024-01-15T12:30:00Z',
    updatedAt: '2024-01-15T12:30:00Z'
  },
  {
    id: '6',
    category: 'Plumbing',
    description: 'Clogged drain in lab',
    status: 'In Progress',
    location: { lat: 17.3865, lng: 78.4875, text: 'Chemistry Lab' },
    createdAt: '2024-01-13T15:00:00Z',
    updatedAt: '2024-01-14T10:00:00Z'
  },
  {
    id: '7',
    category: 'Maintenance',
    description: 'Broken window lock',
    status: 'Resolved',
    location: { lat: 17.3852, lng: 78.4865, text: 'Library East Wing' },
    createdAt: '2024-01-08T14:00:00Z',
    updatedAt: '2024-01-09T11:00:00Z'
  },
  {
    id: '8',
    category: 'Electrical',
    description: 'Power outlet not working',
    status: 'Closed',
    location: { lat: 17.3875, lng: 78.4885, text: 'Computer Lab 3' },
    createdAt: '2024-01-03T10:00:00Z',
    updatedAt: '2024-01-04T09:00:00Z'
  },
  {
    id: '9',
    category: 'Sanitation',
    description: 'Need more hand sanitizers',
    status: 'Open',
    location: { lat: 17.3858, lng: 78.4868, text: 'Medical Center' },
    createdAt: '2024-01-15T08:00:00Z',
    updatedAt: '2024-01-15T08:00:00Z'
  },
  {
    id: '10',
    category: 'Plumbing',
    description: 'Tap handle broken',
    status: 'Closed',
    location: { lat: 17.3845, lng: 78.4855, text: 'Sports Complex' },
    createdAt: '2024-01-01T11:00:00Z',
    updatedAt: '2024-01-02T14:00:00Z'
  }
];

const sampleNotifications = [
  {
    id: '1',
    title: 'New Issue Reported',
    message: 'Electrical issue reported near Main Building Entrance',
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString()
  },
  {
    id: '2',
    title: 'Issue Resolved',
    message: 'Plumbing issue in Science Block has been resolved',
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString()
  },
  {
    id: '3',
    title: 'Status Updated',
    message: 'Maintenance issue moved to In Progress',
    read: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString()
  },
  {
    id: '4',
    title: 'New Comment',
    message: 'Admin commented on your issue report',
    read: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString()
  }
];

export { sampleIssues, sampleNotifications };
