PRAGMA foreign_keys=true;

-- half groups
-- id is their chat_id
-- name is the title of the group 
create table groups(
	id  integer NOT NULL PRIMARY KEY,
	name text,
	short_id text NOT NULL UNIQUE -- a 5 digit id to make life easier for both teachers & students.
);

-- a halfMember is a private user of the bot
-- that can send to a half group (simplex communication)
-- id is the chat_id
-- name is the name of the member
create table halfMember(
	id integer NOT NULL PRIMARY KEY,
	name text
);

create table groups_halfMember(
	groupid integer NOT NULL,
	halfMemberid integer NOT NULL,
	PRIMARY KEY (groupid, halfMemberid),
	FOREIGN KEY (groupid) REFERENCES groups (id) 
            ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY (halfMemberid) REFERENCES halfMember (id) 
            ON DELETE CASCADE ON UPDATE CASCADE 
);
