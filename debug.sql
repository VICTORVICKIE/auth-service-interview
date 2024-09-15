SELECT 
    "user".id AS user_id,
    "user".email AS user_email,
    -- "user".profile AS user_profile,
    -- "user".status AS user_status,
    -- "user".created_at AS user_created_at,
    -- "user".updated_at AS user_updated_at,
    
    "organisation".id AS organisation_id,
    "organisation".name AS organisation_name,
    "organisation".status AS organisation_status,
    -- "organisation".personal AS organisation_personal,
    -- "organisation".settings AS organisation_settings,
    -- "organisation".created_at AS organisation_created_at,
    -- "organisation".updated_at AS organisation_updated_at,
    
    "role".id AS role_id,
    "role".name AS role_name,
    "role".description AS role_description
    
    -- "member".status AS member_status,
    -- "member".settings AS member_settings,
    -- "member".created_at AS member_created_at,
    -- "member".updated_at AS member_updated_at
    
FROM 
    "user"
JOIN 
    "member" ON "user".id = "member".user_id
JOIN 
    "organisation" ON "member".org_id = "organisation".id
JOIN 
    "role" ON "member".role_id = "role".id
ORDER BY 
    "user".id, "organisation".id;
