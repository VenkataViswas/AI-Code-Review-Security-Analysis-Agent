// Security issue: SQL injection via concatenated user input.
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

class AccountLookup {
    public ResultSet findAccount(Connection connection, String name) throws SQLException {
        Statement statement = connection.createStatement();
        String sql = "SELECT * FROM accounts WHERE name = '" + name + "'";
        return statement.executeQuery(sql);
    }
}
