package com.example.student.repository;

import com.example.student.model.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface StudentRepository extends JpaRepository<Student, Long> {

    List<Student> findByNameContaining(String keyword);

    Student findByStudentNo(String studentNo);
}
