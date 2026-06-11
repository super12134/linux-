package com.example.student.controller;

import com.example.student.model.Student;
import com.example.student.repository.StudentRepository;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.List;

@Controller
@RequestMapping("/students")
public class StudentController {

    private final StudentRepository studentRepository;

    public StudentController(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    /**
     * 学生列表页
     */
    @GetMapping
    public String list(Model model) {
        List<Student> students = studentRepository.findAll();
        model.addAttribute("students", students);
        model.addAttribute("student", new Student());
        return "index";
    }

    /**
     * 搜索学生
     */
    @GetMapping("/search")
    public String search(@RequestParam("keyword") String keyword, Model model) {
        List<Student> students = studentRepository.findByNameContaining(keyword);
        model.addAttribute("students", students);
        model.addAttribute("student", new Student());
        model.addAttribute("keyword", keyword);
        return "index";
    }

    /**
     * 新增学生
     */
    @PostMapping
    public String add(@ModelAttribute Student student, RedirectAttributes redirectAttributes) {
        if (studentRepository.findByStudentNo(student.getStudentNo()) != null) {
            redirectAttributes.addFlashAttribute("error", "学号已存在：" + student.getStudentNo());
            return "redirect:/students";
        }
        studentRepository.save(student);
        redirectAttributes.addFlashAttribute("success", "添加学生成功");
        return "redirect:/students";
    }

    /**
     * 跳转编辑页
     */
    @GetMapping("/edit/{id}")
    public String edit(@PathVariable Long id, Model model) {
        Student student = studentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("无效学生ID：" + id));
        List<Student> students = studentRepository.findAll();
        model.addAttribute("students", students);
        model.addAttribute("student", student);
        model.addAttribute("editMode", true);
        return "index";
    }

    /**
     * 更新学生信息
     */
    @PostMapping("/update/{id}")
    public String update(@PathVariable Long id, @ModelAttribute Student updated,
                         RedirectAttributes redirectAttributes) {
        Student student = studentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("无效学生ID：" + id));
        student.setName(updated.getName());
        student.setStudentNo(updated.getStudentNo());
        student.setGender(updated.getGender());
        student.setAge(updated.getAge());
        student.setMajor(updated.getMajor());
        studentRepository.save(student);
        redirectAttributes.addFlashAttribute("success", "更新学生信息成功");
        return "redirect:/students";
    }

    /**
     * 删除学生
     */
    @GetMapping("/delete/{id}")
    public String delete(@PathVariable Long id, RedirectAttributes redirectAttributes) {
        studentRepository.deleteById(id);
        redirectAttributes.addFlashAttribute("success", "删除学生成功");
        return "redirect:/students";
    }
}
