package com.veloxa.cockpit.employeeagent.repository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.veloxa.cockpit.employeeagent.entity.ExtractedRecord;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;
import org.springframework.data.repository.query.Param;

public interface ExtractedRecordRepository
        extends Repository<ExtractedRecord, UUID> {

    Optional<ExtractedRecord> findById(UUID id);

    @Query(value = """
            SELECT *
            FROM extracted_record
            WHERE record_key LIKE 'Employees:%'
              AND extracted_data ->> 'record_status' = 'DATA'
              AND extracted_data #>> '{data,Emp ID}' IN (:employeeCodes)
            ORDER BY extracted_data #>> '{data,Emp ID}'
            """, nativeQuery = true)
    List<ExtractedRecord> findEmployeeMasterRecordsByEmployeeCodes(
            @Param("employeeCodes") Collection<String> employeeCodes
    );
}