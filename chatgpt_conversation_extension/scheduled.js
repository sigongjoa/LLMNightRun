document.addEventListener('DOMContentLoaded', function() {
  const messageInput = document.getElementById('message');
  const scheduleTimeInput = document.getElementById('schedule-time');
  const addScheduleBtn = document.getElementById('add-schedule-btn');
  const scheduledItemsContainer = document.getElementById('scheduled-items');
  const statusDiv = document.getElementById('status');
  
  let scheduledMessages = [];
  
  // Set minimum time to current time
  const now = new Date();
  now.setMinutes(now.getMinutes() + 1); // Add 1 minute to avoid immediate scheduling
  const formattedNow = now.toISOString().slice(0, 16);
  scheduleTimeInput.min = formattedNow;
  scheduleTimeInput.value = formattedNow;
  
  // Check if we're on a ChatGPT/Claude page
  console.log('Checking if we are on scheduled page');
  // 이 페이지는 항상 확장 프로그램 내부 페이지이미로 별도의 제한이 필요하지 않음
  statusDiv.textContent = '예약 메시지를 관리하는 페이지입니다. 여기서 예약을 추가하고 관리할 수 있습니다.';
  
  // Load saved scheduled messages
  chrome.storage.local.get('scheduledMessages', function(data) {
    console.log('Loaded scheduled messages from storage:', data);
    if (data.scheduledMessages) {
      scheduledMessages = data.scheduledMessages;
      updateScheduledList();
    }
  });
  
  // Handle add schedule button click
  addScheduleBtn.addEventListener('click', function() {
    console.log('Add schedule button clicked');
    
    const message = messageInput.value.trim();
    const scheduleTime = scheduleTimeInput.value;
    
    if (!message) {
      showStatus('메시지 내용을 입력해주세요.', true);
      return;
    }
    
    if (!scheduleTime) {
      showStatus('예약 시간을 선택해주세요.', true);
      return;
    }
    
    const scheduleDate = new Date(scheduleTime);
    const now = new Date();
    
    if (scheduleDate <= now) {
      showStatus('예약 시간은 현재 시간보다 이후여야 합니다.', true);
      return;
    }
    
    // Add the scheduled message
    const id = Date.now().toString();
    const scheduledMessage = {
      id: id,
      message: message,
      scheduleTime: scheduleDate.toISOString(),
      status: 'scheduled'
    };
    
    scheduledMessages.push(scheduledMessage);
    saveScheduledMessages();
    updateScheduledList();
    
    // Set up an alarm for this message
    chrome.alarms.create(`scheduled-message-${id}`, {
      when: scheduleDate.getTime()
    });
    
    console.log('Alarm created for message:', scheduledMessage);
    
    // Reset form
    messageInput.value = '';
    
    showStatus('메시지가 예약되었습니다.', false);
  });
  
  // Function to display scheduled messages
  function updateScheduledList() {
    console.log('Updating scheduled messages list');
    
    // Clear current list (except the template)
    while (scheduledItemsContainer.children.length > 1) {
      scheduledItemsContainer.removeChild(scheduledItemsContainer.lastChild);
    }
    
    // Sort by schedule time
    scheduledMessages.sort((a, b) => new Date(a.scheduleTime) - new Date(b.scheduleTime));
    
    // Add each scheduled message
    scheduledMessages.forEach(function(item) {
      const scheduleDate = new Date(item.scheduleTime);
      const template = scheduledItemsContainer.firstElementChild.cloneNode(true);
      
      template.style.display = '';
      template.id = `schedule-${item.id}`;
      template.querySelector('.scheduled-time').textContent = `예약 시간: ${scheduleDate.toLocaleString()}`;
      template.querySelector('.scheduled-message').textContent = item.message;
      
      // Add delete button functionality
      const removeBtn = template.querySelector('.remove-btn');
      removeBtn.addEventListener('click', function() {
        removeScheduledMessage(item.id);
      });
      
      // Add status indicator if needed
      if (item.status === 'sent') {
        template.style.backgroundColor = '#e8f5e9';
        const statusElement = document.createElement('div');
        statusElement.textContent = '전송됨';
        statusElement.style.color = '#4caf50';
        statusElement.style.fontWeight = 'bold';
        template.appendChild(statusElement);
      }
      
      scheduledItemsContainer.appendChild(template);
    });
    
    console.log('Scheduled messages list updated with', scheduledMessages.length, 'items');
  }
  
  // Function to save scheduled messages to chrome storage
  function saveScheduledMessages() {
    console.log('Saving scheduled messages to storage:', scheduledMessages);
    chrome.storage.local.set({'scheduledMessages': scheduledMessages});
  }
  
  // Function to remove a scheduled message
  function removeScheduledMessage(id) {
    console.log('Removing scheduled message:', id);
    
    // Remove the alarm
    chrome.alarms.clear(`scheduled-message-${id}`);
    
    // Remove from storage
    scheduledMessages = scheduledMessages.filter(item => item.id !== id);
    saveScheduledMessages();
    updateScheduledList();
    
    showStatus('예약이 취소되었습니다.', false);
  }
  
  // Function to display status messages
  function showStatus(message, isError) {
    statusDiv.textContent = message;
    
    if (isError) {
      statusDiv.classList.add('error');
    } else {
      statusDiv.classList.remove('error');
    }
    
    // Clear status after 3 seconds
    setTimeout(function() {
      statusDiv.textContent = '메시지 예약 준비가 되었습니다.';
      statusDiv.classList.remove('error');
    }, 3000);
  }
  
  // Check for existing alarms
  chrome.alarms.getAll(function(alarms) {
    console.log('Current alarms:', alarms);
  });
  
  console.log('Scheduled.js initialization complete');
});
