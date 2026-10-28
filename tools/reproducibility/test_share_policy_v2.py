"""Small policy-discovery fixtures, run only in PBS."""
import unittest
import share_policy_v2 as policy


class PolicyTests(unittest.TestCase):
    def test_paths_owners_hosts_and_job_suffixes(self):
        docs=[dict(Job_Owner='alice@login-host',hostname='ComputeRack002',exec_host='compute-host/0+other-host/0',
                   exec_vnode='(compute-host:ncpus=1)',job_id='123.scheduler-host',
                   path='/home/alice/work/f.py', windows=r'C:\Users\bob\work')]
        result=policy.derive_policy(docs,["ROOT='/home/alice/work'\nSERVER='ComputeRack001'\n"])
        paths={r['private'] for r in result['path_prefixes']}
        ids={r['private'] for r in result['identifiers']}
        self.assertIn('/home/alice',paths);self.assertIn('alice',ids);self.assertIn('bob',ids)
        self.assertTrue({'login-host','compute-host','other-host','scheduler-host','ComputeRack001'}<=ids)

    def test_deterministic_and_no_hash_as_identity(self):
        docs=[dict(path='/home/example/a',sha256='a'*64,hostname='node1')]
        one=policy.derive_policy(docs,[]);two=policy.derive_policy(list(reversed(docs)),[])
        self.assertEqual(one,two)
        self.assertNotIn('a'*64,{r['private'] for r in one['identifiers']})

    def test_windows_escaped_variants_and_posix_sample_paths(self):
        result=policy.derive_policy([],['"C:\\\\Users\\\\alice\\\\file"',"'/home/<user>/example'"])
        self.assertIn('/home/<user>',{r['private'] for r in result['path_prefixes']})
        self.assertIn('alice',{r['private'] for r in result['identifiers']})


if __name__=='__main__':unittest.main()
