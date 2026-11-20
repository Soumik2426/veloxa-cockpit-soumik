package com.veloxa.cockpit.data;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/api/v1/data-files")
public class DataFileController {

    private final JdbcTemplate jdbcTemplate;
    private final Path dataRoot;

    public DataFileController(
            JdbcTemplate jdbcTemplate,
            @Value("${data.root:./data/input/Veloxa_Hackathon_Release_Packs}") String dataRoot
    ) {
        this.jdbcTemplate = jdbcTemplate;
        this.dataRoot = Paths.get(dataRoot).toAbsolutePath().normalize();
    }

    @GetMapping
    public List<DataFileResponse> listFiles() {
        return jdbcTemplate.query(
                """
                SELECT id, file_name, relative_path, file_extension, file_type,
                       status, file_size, discovered_at, processed_at
                FROM ingestion_file
                ORDER BY relative_path
                """,
                (rs, rowNum) -> new DataFileResponse(
                        rs.getObject("id", UUID.class),
                        rs.getString("file_name"),
                        rs.getString("relative_path"),
                        rs.getString("file_extension"),
                        rs.getString("file_type"),
                        categoryFor(rs.getString("relative_path")),
                        rs.getString("status"),
                        rs.getLong("file_size"),
                        rs.getObject("discovered_at", java.time.OffsetDateTime.class),
                        rs.getObject("processed_at") == null
                                ? null
                                : rs.getObject("processed_at", java.time.OffsetDateTime.class)
                )
        );
    }

    @GetMapping("/{fileId}/content")
    public ResponseEntity<Resource> download(@PathVariable UUID fileId) {
        String relativePath = jdbcTemplate.query(
                "SELECT relative_path FROM ingestion_file WHERE id = ?",
                statement -> statement.setObject(1, fileId),
                (rs, rowNum) -> rs.getString("relative_path")
        ).stream().findFirst().orElseThrow(() ->
                new ResponseStatusException(NOT_FOUND, "Source file was not found.")
        );

        Path file = dataRoot.resolve(relativePath).normalize();
        if (!file.startsWith(dataRoot) || !Files.isRegularFile(file)) {
            throw new ResponseStatusException(NOT_FOUND, "Source file is unavailable.");
        }

        try {
            Resource resource = new UrlResource(file.toUri());
            String contentType = Files.probeContentType(file);
            MediaType mediaType = contentType == null
                    ? MediaType.APPLICATION_OCTET_STREAM
                    : MediaType.parseMediaType(contentType);

            return ResponseEntity.ok()
                    .contentType(mediaType)
                    .header(
                            HttpHeaders.CONTENT_DISPOSITION,
                            "inline; filename=\"" + file.getFileName() + "\""
                    )
                    .body(resource);
        } catch (Exception exception) {
            throw new ResponseStatusException(
                    NOT_FOUND,
                    "Source file could not be opened.",
                    exception
            );
        }
    }

    private static String categoryFor(String relativePath) {
        String normalized = relativePath.replace('\\', '/').toLowerCase();
        if (normalized.contains("/hr/")) return "HR";
        if (normalized.contains("/finance/")) return "Finance";
        if (normalized.contains("/engineering/")) return "Engineering";
        if (normalized.contains("/email/")) return "Emails";
        if (normalized.contains("/transcripts/")) return "Transcripts";
        return "Documents";
    }

    public record DataFileResponse(
            UUID id,
            String fileName,
            String relativePath,
            String extension,
            String fileType,
            String category,
            String status,
            long fileSize,
            java.time.OffsetDateTime discoveredAt,
            java.time.OffsetDateTime processedAt
    ) {
    }
}
