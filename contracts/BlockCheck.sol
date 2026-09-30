// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title BlockCheck
 * @notice Simple blockchain-based event registration and attendance DApp.
 *
 * Demo flow:
 * 1. Any wallet can create an event and becomes its organizer.
 * 2. Users register themselves.
 * 3. Registered users check themselves in.
 * 4. Registration and attendance remain publicly verifiable on-chain.
 */
contract BlockCheck {
    struct EventInfo {
        uint256 id;
        string name;
        uint256 eventTime;
        address organizer;
        uint256 registeredCount;
        uint256 checkedInCount;
        bool active;
    }

    uint256 public eventCount;

    mapping(uint256 => EventInfo) private events;
    mapping(uint256 => mapping(address => bool)) private registrations;
    mapping(uint256 => mapping(address => bool)) private attendance;

    event EventCreated(
        uint256 indexed eventId,
        string name,
        uint256 eventTime,
        address indexed organizer
    );

    event Registered(
        uint256 indexed eventId,
        address indexed attendee
    );

    event CheckedIn(
        uint256 indexed eventId,
        address indexed attendee,
        uint256 timestamp
    );

    event EventStatusChanged(
        uint256 indexed eventId,
        bool active
    );

    modifier validEvent(uint256 eventId) {
        require(eventId > 0 && eventId <= eventCount, "Event does not exist");
        _;
    }

    modifier onlyOrganizer(uint256 eventId) {
        require(events[eventId].organizer == msg.sender, "Organizer only");
        _;
    }

    function createEvent(
        string calldata name,
        uint256 eventTime
    ) external returns (uint256) {
        require(bytes(name).length > 0, "Event name required");
        require(bytes(name).length <= 100, "Event name too long");
        require(eventTime > block.timestamp, "Event time must be in future");

        eventCount += 1;

        events[eventCount] = EventInfo({
            id: eventCount,
            name: name,
            eventTime: eventTime,
            organizer: msg.sender,
            registeredCount: 0,
            checkedInCount: 0,
            active: true
        });

        emit EventCreated(eventCount, name, eventTime, msg.sender);
        return eventCount;
    }

    function register(uint256 eventId)
        external
        validEvent(eventId)
    {
        EventInfo storage eventInfo = events[eventId];

        require(eventInfo.active, "Event is inactive");
        require(block.timestamp < eventInfo.eventTime, "Registration closed");
        require(!registrations[eventId][msg.sender], "Already registered");

        registrations[eventId][msg.sender] = true;
        eventInfo.registeredCount += 1;

        emit Registered(eventId, msg.sender);
    }

    function checkIn(uint256 eventId)
        external
        validEvent(eventId)
    {
        EventInfo storage eventInfo = events[eventId];

        require(eventInfo.active, "Event is inactive");
        require(registrations[eventId][msg.sender], "Register first");
        require(!attendance[eventId][msg.sender], "Already checked in");

        attendance[eventId][msg.sender] = true;
        eventInfo.checkedInCount += 1;

        emit CheckedIn(eventId, msg.sender, block.timestamp);
    }

    function setEventActive(
        uint256 eventId,
        bool active
    )
        external
        validEvent(eventId)
        onlyOrganizer(eventId)
    {
        events[eventId].active = active;
        emit EventStatusChanged(eventId, active);
    }

    function getEvent(uint256 eventId)
        external
        view
        validEvent(eventId)
        returns (EventInfo memory)
    {
        return events[eventId];
    }

    function getMyStatus(uint256 eventId)
        external
        view
        validEvent(eventId)
        returns (bool registered, bool checkedIn)
    {
        return (
            registrations[eventId][msg.sender],
            attendance[eventId][msg.sender]
        );
    }

    function getUserStatus(
        uint256 eventId,
        address user
    )
        external
        view
        validEvent(eventId)
        returns (bool registered, bool checkedIn)
    {
        return (
            registrations[eventId][user],
            attendance[eventId][user]
        );
    }
}
