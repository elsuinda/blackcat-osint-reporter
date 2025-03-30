import ldap
from flask import current_app, flash
from . import login_manager
from app.models import User

def init_ldap(app):
    app.config['LDAP_SERVER'] = app.config.get('LDAP_SERVER', 'ldap://localhost')
    app.config['LDAP_USER_OU'] = app.config.get('LDAP_USER_OU', 'ou=users,dc=example,dc=com')
    app.config['LDAP_GROUP_OU'] = app.config.get('LDAP_GROUP_OU', 'ou=groups,dc=example,dc=com')
    app.config['LDAP_ADMIN_GROUP'] = app.config.get('LDAP_ADMIN_GROUP', 'cn=admins,ou=groups,dc=example,dc=com')
    app.config['LDAP_USER_GROUP'] = app.config.get('LDAP_USER_GROUP', 'cn=users,ou=groups,dc=example,dc=com')
    app.config['LDAP_BIND_DN'] = app.config.get('LDAP_BIND_DN', 'cn=admin,dc=example,dc=com')
    app.config['LDAP_BIND_PASSWORD'] = app.config.get('LDAP_BIND_PASSWORD', 'password')

def ldap_connect():
    try:
        ldap_conn = ldap.initialize(current_app.config['LDAP_SERVER'])
        ldap_conn.simple_bind_s(
            current_app.config['LDAP_BIND_DN'],
            current_app.config['LDAP_BIND_PASSWORD']
        )
        return ldap_conn
    except ldap.LDAPError as e:
        current_app.logger.error(f"LDAP connection error: {e}")
        return None

def ldap_authenticate(username, password):
    ldap_conn = ldap_connect()
    if not ldap_conn:
        return None
    
    try:
        user_dn = f"uid={username},{current_app.config['LDAP_USER_OU']}"
        ldap_conn.simple_bind_s(user_dn, password)
        
        # Check group membership
        admin_filter = f"(&(memberUid={username})(objectClass=posixGroup))"
        admin_groups = ldap_conn.search_s(
            current_app.config['LDAP_GROUP_OU'],
            ldap.SCOPE_SUBTREE,
            admin_filter
        )
        
        is_admin = any(
            group[0] == current_app.config['LDAP_ADMIN_GROUP'] 
            for group in admin_groups
        )
        
        # Get user info
        user_filter = f"(uid={username})"
        user_info = ldap_conn.search_s(
            current_app.config['LDAP_USER_OU'],
            ldap.SCOPE_SUBTREE,
            user_filter
        )
        
        if not user_info:
            return None
            
        user_attrs = user_info[0][1]
        email = user_attrs.get('mail', [b''])[0].decode('utf-8')
        full_name = user_attrs.get('cn', [b''])[0].decode('utf-8')
        
        # Create or update user in local DB
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_ldap=True,
                is_admin=is_admin
            )
            db.session.add(user)
        else:
            user.email = email
            user.full_name = full_name
            user.is_admin = is_admin
        
        db.session.commit()
        return user
        
    except ldap.INVALID_CREDENTIALS:
        current_app.logger.warning(f"Invalid LDAP credentials for user {username}")
        return None
    except ldap.LDAPError as e:
        current_app.logger.error(f"LDAP authentication error: {e}")
        return None
    finally:
        ldap_conn.unbind()
