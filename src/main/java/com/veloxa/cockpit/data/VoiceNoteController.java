package com.veloxa.cockpit.data;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/voice-notes")
public class VoiceNoteController {

    private static final Pattern NOTE_ID = Pattern.compile("^(T6[abcd])_");

    private static final Map<String, Outcome> OUTCOMES = Map.of(
            "T6a", new Outcome(
                    "implemented",
                    "Implemented",
                    "The Risk Monitor generates an evidence-backed risk assessment automatically on page load.",
                    "The assessment remains dynamic and uses the existing retrieval service."
            ),
            "T6b", new Outcome(
                    "pushback",
                    "Written pushback",
                    "The reporting change has no confirmed effective date, so current employee and department records are not rewritten.",
                    "The proposed change remains unresolved until an authoritative HR or leadership record confirms it."
            ),
            "T6c", new Outcome(
                    "pushback",
                    "Written pushback",
                    "The request for speculative individual profiling and private communications is declined.",
                    "The cockpit provides aggregate workforce indicators instead of private messages or individual quit predictions."
            ),
            "T6d", new Outcome(
                    "implemented",
                    "Implemented with evidence guardrails",
                    "Company questions can cross-check employee, engineering, project and transcript evidence before assessing the reported resignation's impact.",
                    "No ownership change is applied until the identity, notice period and last working day are reconciled."
            )
    );

    private final JdbcTemplate jdbcTemplate;
    private final Path dataRoot;

    public VoiceNoteController(
            JdbcTemplate jdbcTemplate,
            @Value("${data.root:./data/input/Veloxa_Hackathon_Release_Packs}") String dataRoot
    ) {
        this.jdbcTemplate = jdbcTemplate;
        this.dataRoot = Paths.get(dataRoot).toAbsolutePath().normalize();
    }

    @GetMapping
    public List<VoiceNoteResponse> listVoiceNotes() {
        return jdbcTemplate.query(
                """
                SELECT id, file_name, relative_path, discovered_at
                FROM ingestion_file
                WHERE file_name LIKE 'T6%CEO_Voice_Note.docx'
                ORDER BY file_name
                """,
                (rs, rowNum) -> {
                    UUID id = rs.getObject("id", UUID.class);
                    String fileName = rs.getString("file_name");
                    String noteId = NOTE_ID.matcher(fileName).find()
                            ? fileName.substring(0, 3)
                            : fileName;
                    Outcome outcome = OUTCOMES.getOrDefault(
                            noteId,
                            new Outcome(
                                    "pending",
                                    "Pending",
                                    "No recorded outcome is available.",
                                    "Review the source note and decision log."
                            )
                    );
                    return new VoiceNoteResponse(
                            id,
                            noteId,
                            fileName,
                            rs.getString("relative_path"),
                            rs.getObject("discovered_at", java.time.OffsetDateTime.class),
                            extractTranscript(rs.getString("relative_path")),
                            outcome
                    );
                }
        );
    }

    private String extractTranscript(String relativePath) {
        Path file = dataRoot.resolve(relativePath).normalize();
        if (!file.startsWith(dataRoot) || !Files.isRegularFile(file)) {
            return "The original transcript could not be opened.";
        }

        try (InputStream input = Files.newInputStream(file);
             XWPFDocument document = new XWPFDocument(input)) {
            return document.getParagraphs().stream()
                    .map(paragraph -> paragraph.getText().trim())
                    .filter(text -> !text.isBlank())
                    .reduce((left, right) -> left + " " + right)
                    .orElse("The source transcript is empty.");
        } catch (Exception exception) {
            return "The original transcript could not be extracted.";
        }
    }

    public record VoiceNoteResponse(
            UUID id,
            String noteId,
            String sourceFile,
            String relativePath,
            java.time.OffsetDateTime discoveredAt,
            String transcript,
            Outcome outcome
    ) {
    }

    public record Outcome(
            String kind,
            String label,
            String summary,
            String decision
    ) {
    }
}
